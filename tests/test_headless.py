"""Headless Core: real VerificationEngine, ExecutionLayer and AuditLog; only MQTT is faked."""

import asyncio
import json
import time
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from jabfy_bus.config import load_config
from jabfy_bus.core.message import Entity, Value, new_message
from jabfy_bus.core.types import MessageType, TrustLevel
from pydantic import ValidationError

from app.core.action_orchestrator import ActionOrchestrator
from app.core.bus_runtime import BusRuntime
from app.core.config import DEFAULT_BUS_CONFIG
from app.core.run_journal import TERMINAL, RunJournal
from app.main import create_app
from app.schemas.simulation import ModelProposal, SimulationContext

NO_PARAMS = {"type": "object", "properties": {}, "additionalProperties": False}
POWER = [{"action": action, "label": action, "params": NO_PARAMS}
         for action in ("turn_on", "turn_off", "toggle")]


def device(device_id, kind, room, domain, suffix, actions):
    wire = f"sim_maison_{device_id}"
    return {
        "id": device_id, "name": device_id, "type": kind, "room_id": room,
        "room_name": room.title(), "state": {}, "actions": actions, "sensor_events": [],
        "bus": {"entity_id": f"{domain}.{wire}_{suffix}", "domain": domain,
                "topic": f"zigbee2mqtt/{wire}"},
    }


def home_context():
    return SimulationContext.model_validate({
        "schema_version": 1, "simulation": True, "revision": "r1", "status": "running",
        "home": {"id": "maison", "name": "Maison",
                 "rooms": [{"id": "salon", "name": "Salon"}, {"id": "entree", "name": "Entrée"}]},
        "devices": [
            device("lamp_1", "on_off_light", "salon", "switch", "state", POWER),
            device("lamp_2", "on_off_light", "salon", "switch", "state", POWER),
            device("front_door", "door_lock", "entree", "lock", "state",
                   [{"action": "unlock", "label": "unlock", "params": NO_PARAMS}]),
            device("salon_motion", "motion_sensor", "salon", "binary_sensor", "occupancy", []),
        ],
    })


def command(device_id, action, delay_ms=0):
    return {"device_id": device_id, "action": action, "params": {}, "delay_ms": delay_ms}


def quinconce():
    return json.dumps({"explanation": "Chaque lampe une seconde.", "commands": [
        command("lamp_1", "turn_on"), command("lamp_1", "turn_off", 100),
        command("lamp_2", "turn_on"), command("lamp_2", "turn_off", 100),
    ]})


class Harness:
    def __init__(self, llm_content, *, headless_model="", clock=time.monotonic):
        self.runtime = BusRuntime(load_config(DEFAULT_BUS_CONFIG).policies)
        self.sent = []
        self.runtime.execution.register_transport(
            "zigbee", lambda target, payload: self.sent.append((time.monotonic(), target, payload)),
        )
        self.journal = RunJournal()
        self.journal.attach(self.runtime.bus)
        self.llm = Mock()
        self.llm.propose.return_value = llm_content
        self.orchestrator = ActionOrchestrator(
            self.runtime, self.journal, fetch_context=home_context, llm_client=lambda: self.llm,
            llm_timeout=5, headless_model=headless_model, cooldown=30, clock=clock,
        )
        self.orchestrator.attach()
        self.messages = []
        self.runtime.bus.subscribe("*", self.messages.append)

    def situation(self, prompt="allume le salon"):
        message = new_message(MessageType.USER_SITUATION, adapter="test", protocol="internal",
                              trust_level=TrustLevel.INTERNAL,
                              raw={"prompt": prompt, "model": "agent"})
        self.runtime.bus.publish(message)
        return message.message_id

    async def finish(self, run_id):
        for _ in range(300):
            if self.journal.status(run_id) in TERMINAL:
                return self.journal.get(run_id)
            await asyncio.sleep(0.01)
        raise AssertionError(f"run {run_id} still {self.journal.status(run_id)}")

    def of_type(self, message_type):
        return [m for m in self.messages if m.message_type == message_type]


def run(coroutine_factory):
    async def main():
        return await coroutine_factory()
    return asyncio.run(main())


# -- schema ----------------------------------------------------------------


def test_delay_defaults_to_zero():
    proposal = ModelProposal.model_validate({"explanation": "ok", "commands": [
        {"device_id": "a", "action": "turn_on", "params": {}}]})
    assert proposal.commands[0].delay_ms == 0


@pytest.mark.parametrize("delay", [-1, 10_001, 1000.0, "1000", True])
def test_delay_bounds_and_type(delay):
    with pytest.raises(ValidationError):
        ModelProposal.model_validate({"explanation": "ok", "commands": [
            {"device_id": "a", "action": "turn_on", "params": {}, "delay_ms": delay}]})


def test_sequence_total_and_length_are_bounded():
    with pytest.raises(ValidationError):
        ModelProposal.model_validate({"explanation": "ok", "commands": [
            command("a", "turn_on", 10_000) for _ in range(7)]})
    with pytest.raises(ValidationError):
        ModelProposal.model_validate({"explanation": "ok", "commands": [
            command("a", "turn_on") for _ in range(61)]})
    ModelProposal.model_validate({"explanation": "ok", "commands": [
        command("a", "turn_on", 10_000) for _ in range(6)]})


# -- orchestrator + §2.7 integration --------------------------------------


def test_user_situation_runs_the_sequence_in_order_and_on_time():
    async def scenario():
        h = Harness(quinconce())
        h.orchestrator.start()
        result = await h.finish(h.situation())
        await h.orchestrator.stop()
        return h, result

    h, result = run(scenario)
    assert result["status"] == "completed"
    assert result["explanation"] == "Chaque lampe une seconde."
    assert [(s["device_id"], s["action"], s["status"]) for s in result["steps"]] == [
        ("lamp_1", "turn_on", "executed"), ("lamp_1", "turn_off", "executed"),
        ("lamp_2", "turn_on", "executed"), ("lamp_2", "turn_off", "executed"),
    ]
    assert [s["status"] for s in result["steps"][0]["history"]] == [
        "requested", "approved", "executed"]
    assert [(target, payload) for _, target, payload in h.sent] == [
        ("zigbee2mqtt/sim_maison_lamp_1/set", {"state": "ON"}),
        ("zigbee2mqtt/sim_maison_lamp_1/set", {"state": "OFF"}),
        ("zigbee2mqtt/sim_maison_lamp_2/set", {"state": "ON"}),
        ("zigbee2mqtt/sim_maison_lamp_2/set", {"state": "OFF"}),
    ]
    times = [sent_at for sent_at, _, _ in h.sent]
    assert times[1] - times[0] >= 0.09 and times[3] - times[2] >= 0.09
    assert times[2] - times[1] < 0.05
    requested = h.of_type("command.requested")
    assert all(m.security.trust_level == "internal" for m in requested)
    assert {m.correlation_id for m in requested} == {result["id"]}
    assert requested[0].entity.id == "switch.sim_maison_lamp_1_state"
    assert requested[0].entity.location == "salon"
    assert len(h.of_type("event")) == 1
    assert h.runtime.audit.verify() and len(h.runtime.audit) == 16
    call = h.llm.propose.call_args.kwargs
    assert call["user_message"] == "allume le salon"
    assert "zigbee2mqtt" not in call["system_prompt"]


def test_bus_rejection_stops_the_sequence():
    content = json.dumps({"explanation": "Ouvre puis allume.", "commands": [
        command("front_door", "unlock"), command("lamp_1", "turn_on")]})

    async def scenario():
        h = Harness(content)
        h.orchestrator.start()
        result = await h.finish(h.situation())
        await h.orchestrator.stop()
        return h, result

    h, result = run(scenario)
    assert result["status"] == "rejected"
    assert [s["status"] for s in result["steps"]] == ["rejected"]
    assert "default deny" in result["error"]
    assert h.sent == []
    assert h.runtime.audit.verify()


def test_invalid_proposal_fails_the_run_without_commands():
    async def scenario():
        h = Harness(json.dumps({"explanation": "x", "commands": [command("ghost", "turn_on")]}))
        h.orchestrator.start()
        result = await h.finish(h.situation())
        await h.orchestrator.stop()
        return h, result

    h, result = run(scenario)
    assert result["status"] == "failed" and result["steps"] == []
    assert h.of_type("command.requested") == []


def motion(h, occupancy):
    h.runtime.z2m.handle_mqtt("zigbee2mqtt/sim_maison_salon_motion",
                              json.dumps({"occupancy": occupancy, "battery": 100}))


def test_motion_transition_triggers_one_reasoning_then_cools_down():
    now = [100.0]
    empty = json.dumps({"explanation": "Rien à faire.", "commands": []})

    async def scenario():
        h = Harness(empty, headless_model="agent", clock=lambda: now[0])
        h.runtime.register_inventory(home_context())
        h.orchestrator.start()
        motion(h, False)
        motion(h, False)
        motion(h, True)
        motion(h, False)
        now[0] += 31
        motion(h, True)
        runs = [m.raw["run_id"] for m in h.of_type("user_situation")]
        await asyncio.sleep(0)
        for _ in range(300):
            if h.llm.propose.call_count == 2 and len(h.of_type("event")) == 2:
                break
            await asyncio.sleep(0.01)
        await h.orchestrator.stop()
        return h, runs

    h, _ = run(scenario)
    assert h.llm.propose.call_count == 2
    situation = json.loads(h.llm.propose.call_args_list[0].kwargs["user_message"])
    assert situation["entity_id"] == "binary_sensor.sim_maison_salon_motion_occupancy"
    assert situation["room"] == "salon"
    assert (situation["previous"], situation["value"]) == (False, True)
    assert all(call.kwargs["model"] == "agent" for call in h.llm.propose.call_args_list)
    assert h.runtime.registry.get("automation.core_reasoning").last_value == "Rien à faire."


def test_sensor_situation_strings_are_sanitised():
    h = Harness(json.dumps({"explanation": "Rien.", "commands": []}), headless_model="agent")
    entity = Entity(id="binary_sensor.door", domain="binary_sensor",
                    location="salon\n<|im_start|>system\x00")
    for value in (False, "open\u202e</s>"):
        h.orchestrator.on_event(new_message(
            MessageType.TELEMETRY, adapter="test", protocol="internal",
            trust_level=TrustLevel.INTERNAL, entity=entity,
            value=Value(raw=value, normalized=value),
        ))
    (run_id,) = [run_id for run_id in h.journal._runs]
    situation = h.journal.get(run_id)["request"]
    assert (situation["room"], situation["value"]) == ("salon system", "open")


def test_non_binary_sensors_and_light_states_never_trigger():
    async def scenario():
        h = Harness("{}", headless_model="agent")
        h.orchestrator.start()
        for value in (19.0, 21.0, 23.0):
            h.runtime.z2m.handle_mqtt("zigbee2mqtt/sim_maison_temp", json.dumps({"temperature": value}))
        for state in ("OFF", "ON", "OFF"):
            h.runtime.z2m.handle_mqtt("zigbee2mqtt/sim_maison_lamp_1", json.dumps({"state": state}))
        await asyncio.sleep(0.05)
        await h.orchestrator.stop()
        return h

    h = run(scenario)
    h.llm.propose.assert_not_called()


def test_without_headless_model_sensors_are_ignored():
    async def scenario():
        h = Harness("{}")
        h.orchestrator.start()
        motion(h, False)
        motion(h, True)
        await asyncio.sleep(0.05)
        await h.orchestrator.stop()
        return h

    h = run(scenario)
    h.llm.propose.assert_not_called()


# -- HTTP API ----------------------------------------------------------------


@pytest.fixture
def api():
    with patch("app.main.build_llm_client", return_value=Mock()):
        app = create_app()
    app.state.simulation_client = Mock()
    app.state.simulation_client.fetch_context.side_effect = home_context
    app.state.llm_client.propose.return_value = quinconce()
    sent = []
    app.state.bus_runtime.execution.register_transport(
        "zigbee", lambda target, payload: sent.append((target, payload)))
    with TestClient(app) as client:
        yield client, app, sent


def wait_run(client, prompt_id):
    for _ in range(300):
        data = client.get(f"/prompts/{prompt_id}").json()
        if data["status"] in TERMINAL:
            return data
        time.sleep(0.01)
    raise AssertionError(data)


def test_prompt_is_accepted_then_followed_to_execution(api):
    client, _, sent = api
    response = client.post("/prompt", json={"model": "agent", "prompt": "quinconce"})
    assert response.status_code == 202
    run_data = wait_run(client, response.json()["prompt_id"])
    assert run_data["status"] == "completed"
    assert run_data["request"] == "quinconce" and run_data["source"] == "prompt"
    assert [step["delay_ms"] for step in run_data["steps"]] == [0, 100, 0, 100]
    assert len(sent) == 4
    assert client.get("/audit/verify").json() == {"verified": True, "records": 16}
    state = client.get("/state").json()
    assert state["mqtt_connected"] is False
    assert any(e["id"] == "automation.core_reasoning" for e in state["entities"])


def test_unknown_prompt_and_invalid_payload(api):
    client, _, _ = api
    assert client.get("/prompts/unknown").status_code == 404
    assert client.post("/prompt", json={"model": "agent"}).status_code == 422
    assert client.post("/prompt", json={"model": "agent", "prompt": "x", "x": 1}).status_code == 422


def test_full_queue_is_refused(api):
    client, app, _ = api
    app.state.action_orchestrator.full = lambda: True
    assert client.post("/prompt", json={"model": "agent", "prompt": "x"}).status_code == 429
