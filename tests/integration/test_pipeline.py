"""Full pipeline (MASTER_PLAN §2.7): real Mosquitto, simulator and Core processes.

Core hosts the bus pipeline in process (§2.1), so it plays the role of
`jabfy-bus serve`. Only the model is replaced, by a fixed OpenAI-compatible
answer. Run with:

    JABFY_INTEGRATION=1 pytest tests/integration

Needs Docker (image eclipse-mosquitto:2) and the sibling jabfy-simulation
checkout with its virtualenv (override with JABFY_SIM_DIR).
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import pytest

CORE_DIR = Path(__file__).resolve().parents[2]
SIM_DIR = Path(os.getenv("JABFY_SIM_DIR", CORE_DIR.parent / "jabfy-simulation"))
SIM_BIN = SIM_DIR / ".venv" / "bin" / "jabfy-sim"
MOSQUITTO_CONF = SIM_DIR / "docker" / "mosquitto.conf"

pytestmark = pytest.mark.skipif(
    os.getenv("JABFY_INTEGRATION") != "1", reason="set JABFY_INTEGRATION=1 to run",
)

PROPOSAL = {"explanation": "Mouvement au salon : allumer la lampe.", "commands": [
    {"device_id": "salon_lamp", "action": "turn_on", "params": {}, "delay_ms": 0},
]}


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_until(check, timeout: float, what: str):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            result = check()
        except (httpx.HTTPError, OSError):
            result = None
        if result:
            return result
        time.sleep(0.2)
    raise AssertionError(f"timed out waiting for {what}")


class FakeModel(BaseHTTPRequestHandler):
    def do_GET(self):
        self._reply({"data": [{"id": "agent"}]})

    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        self._reply({"choices": [{"message": {"content": json.dumps(PROPOSAL)}}]})

    def _reply(self, body):
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def stack(tmp_path):
    if shutil.which("docker") is None or not SIM_BIN.exists():
        pytest.fail("Docker and the jabfy-simulation virtualenv are required")
    mqtt_port, sim_port, core_port = free_port(), free_port(), free_port()
    processes, logs = [], []
    container = f"jabfy-it-mosquitto-{mqtt_port}"
    model = ThreadingHTTPServer(("127.0.0.1", 0), FakeModel)
    threading.Thread(target=model.serve_forever, daemon=True).start()

    def spawn(name, command, **kwargs):
        log = open(tmp_path / f"{name}.log", "w")
        logs.append(log)
        processes.append(subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, **kwargs))

    try:
        subprocess.run([
            "docker", "run", "-d", "--rm", "--name", container,
            "-p", f"127.0.0.1:{mqtt_port}:1883",
            "-v", f"{MOSQUITTO_CONF}:/mosquitto/config/mosquitto.conf:ro",
            "eclipse-mosquitto:2",
        ], check=True, capture_output=True)
        wait_until(lambda: socket.create_connection(("127.0.0.1", mqtt_port), timeout=1).close()
                   or True, 30, "Mosquitto")

        home = subprocess.run([
            SIM_DIR / ".venv" / "bin" / "python", "-c",
            "from sim.home import default_home; home = default_home(); "
            "home.automations = []; print(home.model_dump_json())",
        ], check=True, capture_output=True, text=True, cwd=SIM_DIR).stdout
        (tmp_path / "home.json").write_text(home)
        sim_url = f"http://127.0.0.1:{sim_port}"
        spawn("sim", [SIM_BIN, "ui", "--port", str(sim_port),
                      "--broker", f"127.0.0.1:{mqtt_port}",
                      "--home-file", str(tmp_path / "home.json"),
                      "--core-url", f"http://127.0.0.1:{core_port}"], cwd=tmp_path)
        wait_until(lambda: httpx.get(f"{sim_url}/api/state").json()["status"] == "running",
                   30, "the simulator")

        env = {**os.environ,
               "JABFY_LLM_BASE_URL": f"http://127.0.0.1:{model.server_port}/v1",
               "JABFY_LLM_API_KEY": "", "JABFY_LLM_PROVIDER": "openai_compat",
               "JABFY_SIMULATION_URL": sim_url,
               "JABFY_MQTT_BROKER": f"127.0.0.1:{mqtt_port}",
               "JABFY_HEADLESS_MODEL": "agent", "JABFY_HEADLESS_COOLDOWN_SECONDS": "30",
               "JABFY_BUS_CONFIG": str(CORE_DIR / "config" / "bus.json")}
        core_url = f"http://127.0.0.1:{core_port}"
        spawn("core", [sys.executable, "-m", "uvicorn", "app.main:app",
                       "--host", "127.0.0.1", "--port", str(core_port)], cwd=CORE_DIR, env=env)
        wait_until(lambda: httpx.get(f"{core_url}/state").json()["mqtt_connected"], 30, "Core")
        yield sim_url, core_url, core_port
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
        for log in logs:
            log.close()
        subprocess.run(["docker", "stop", container], capture_output=True)
        model.shutdown()


def test_motion_event_crosses_the_whole_pipeline(stack):
    from websockets.sync.client import connect

    sim_url, core_url, core_port = stack
    events, stop = [], threading.Event()

    def listen(ws):
        while not stop.is_set():
            try:
                events.append(json.loads(ws.recv(timeout=0.5)))
            except TimeoutError:
                continue

    with connect(f"ws://127.0.0.1:{core_port}/bus/events") as ws:
        listener = threading.Thread(target=listen, args=(ws,), daemon=True)
        listener.start()
        time.sleep(1)
        assert httpx.post(f"{sim_url}/api/devices/salon_motion/motion",
                          json={"duration_ms": 3000}).status_code == 202

        def executed():
            return [event for event in list(events)
                    if event["message_type"] == "command.executed"]
        (result,) = wait_until(executed, 30, "command.executed")
        time.sleep(0.5)
        stop.set()
        listener.join()

    request_id = result["correlation_id"]
    by_type = {event["message_type"]: event for event in events
               if event["message_id"] == request_id or event["correlation_id"] == request_id}
    assert set(by_type) == {"command.requested", "command.approved", "command.executed"}
    requested = by_type["command.requested"]
    assert requested["entity"]["id"] == "switch.sim_maison_salon_lamp_state"
    assert requested["command"]["action"] == "turn_on"
    assert result["raw"]["success"] is True
    assert any(event["entity"] and event["entity"]["id"]
               == "binary_sensor.sim_maison_salon_motion_occupancy"
               and event["value"]["normalized"] is True for event in events)

    lamp = lambda: next(device for device in httpx.get(f"{sim_url}/api/state").json()["devices"]
                        if device["id"] == "salon_lamp")["state"]["state"] == "ON"
    wait_until(lamp, 10, "the simulated lamp to turn on")

    audit = httpx.get(f"{core_url}/audit/verify").json()
    assert audit["verified"] is True and audit["records"] >= 2
