"""Live-inventory proposals: no simulator, model backend, or device executor required."""

import json
from copy import deepcopy
from unittest.mock import Mock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.errors import LLMClientError
from app.main import create_app
from app.schemas.actions import ActionResponse, VerificationDecision
from app.schemas.simulation import ModelProposal
from app.simulation.client import SimulationClient


@pytest.fixture
def context():
    return {
        "schema_version": 1,
        "home": {
            "id": "custom-home", "name": "Maison personnalisée",
            "rooms": [{"id": "office", "name": "Bureau"}],
        },
        "revision": "revision-1",
        "simulation": True,
        "status": "running",
        "devices": [{
            "id": "desk_strip_42", "name": "Ruban du bureau", "type": "dimmer_light",
            "room_id": "office", "room_name": "Bureau",
            "state": {"state": "OFF", "brightness": 0},
            "actions": [{
                "action": "set_brightness", "label": "Régler la luminosité",
                "params": {
                    "type": "object",
                    "properties": {"brightness": {"type": "integer", "minimum": 0, "maximum": 254}},
                    "required": ["brightness"], "additionalProperties": False,
                },
            }],
            "sensor_events": [],
        }],
    }


def valid_proposal():
    return {"explanation": "Éclairer le bureau.", "commands": [{
        "device_id": "desk_strip_42", "action": "set_brightness", "params": {"brightness": 128},
    }]}


@pytest.fixture
def api(context):
    requests = []

    def transport(request):
        requests.append(request)
        return httpx.Response(200, json=context)

    with patch("app.main.build_llm_client", return_value=Mock()):
        app = create_app()
    app.state.simulation_client = SimulationClient(
        "http://configured-simulation:8080", transport=httpx.MockTransport(transport),
    )
    app.state.llm_client.propose.return_value = json.dumps(valid_proposal())
    with TestClient(app) as client:
        yield client, app, requests
    app.state.llm_client.close.assert_called_once()


def test_home_discovery_uses_only_the_configured_url_and_timeout(api, context):
    client, _, requests = api
    response = client.get("/simulation/home", params={"url": "http://other-host/private"})
    assert response.status_code == 200
    assert response.json() == context
    assert str(requests[0].url) == "http://configured-simulation:8080/api/ai/context"
    assert requests[0].extensions["timeout"]["read"] == 5.0
    assert requests[0].method == "GET"


def test_proposal_uses_fresh_custom_inventory_and_never_executes(api, context):
    client, app, requests = api
    first = client.post("/simulation/propose", json={"model": "local-model", "prompt": "Éclaire le bureau"})
    assert first.status_code == 200
    assert first.json() == {**valid_proposal(), "context_revision": "revision-1"}
    call = app.state.llm_client.propose.call_args.kwargs
    assert call["model"] == "local-model"
    assert call["user_message"] == "Éclaire le bureau"
    assert call["response_schema"] == ModelProposal.model_json_schema()
    assert call["params"].temperature == 0
    assert "desk_strip_42" in call["system_prompt"]
    assert "Ruban du bureau" in call["system_prompt"]
    assert "untrusted data" in call["system_prompt"]
    assert "hallway_light" not in call["system_prompt"]

    context["revision"] = "revision-2"
    context["devices"][0]["name"] = "Nouveau nom"
    second = client.post("/simulation/propose", json={"model": "local-model", "prompt": "Éclaire le bureau"})
    assert second.json()["context_revision"] == "revision-2"
    assert "Nouveau nom" in app.state.llm_client.propose.call_args.kwargs["system_prompt"]
    assert len(requests) == 2
    assert all(request.method == "GET" for request in requests)


@pytest.mark.parametrize("command", [
    {"device_id": "unknown", "action": "set_brightness", "params": {"brightness": 128}},
    {"device_id": "desk_strip_42", "action": "unlock", "params": {}},
    {"device_id": "desk_strip_42", "action": "set_brightness", "params": {"brightness": 255}},
    {"device_id": "desk_strip_42", "action": "set_brightness", "params": {"brightness": -1}},
    {"device_id": "desk_strip_42", "action": "set_brightness", "params": {"brightness": True}},
    {"device_id": "desk_strip_42", "action": "set_brightness", "params": {"brightness": "128"}},
    {"device_id": "desk_strip_42", "action": "set_brightness", "params": {"brightness": 1.5}},
    {"device_id": "desk_strip_42", "action": "set_brightness", "params": {"brightness": 128.0}},
    {"device_id": "desk_strip_42", "action": "set_brightness", "params": {}},
    {"device_id": "desk_strip_42", "action": "set_brightness", "params": {"brightness": 128, "secret": 1}},
])
def test_any_invalid_command_rejects_the_entire_proposal(api, command):
    client, app, _ = api
    proposal = valid_proposal()
    proposal["commands"].append(command)
    app.state.llm_client.propose.return_value = json.dumps(proposal)
    response = client.post("/simulation/propose", json={"model": "local-model", "prompt": "Éclaire"})
    assert response.status_code == 502
    assert "commands" not in response.json()


@pytest.mark.parametrize("content", [
    "not JSON",
    '```json\n{"explanation":"ok","commands":[]}\n```',
    '{"explanation":"ok","commands":"turn_on"}',
    '{"explanation":"ok"}',
    '{"commands":[]}',
    '{"explanation":23,"commands":[]}',
    '{"explanation":"ok","commands":[],"execute":true}',
    '{"explanation":"ok","commands":[{"device_id":"desk_strip_42","action":"set_brightness"}]}',
    '{"explanation":"ok","commands":[{"device_id":"desk_strip_42","action":"set_brightness","params":{"brightness":NaN}}]}',
])
def test_malformed_model_output_is_not_an_executable_success(api, content):
    client, app, _ = api
    app.state.llm_client.propose.return_value = content
    response = client.post("/simulation/propose", json={"model": "local-model", "prompt": "Éclaire"})
    assert response.status_code == 502
    assert "commands" not in response.json()


def test_nested_parameter_schema_is_enforced(api, context):
    client, app, _ = api
    context["devices"][0]["actions"][0] = {
        "action": "set_color", "label": "Couleur",
        "params": {"type": "object", "required": ["color"], "additionalProperties": False,
                   "properties": {"color": {"$ref": "#/$defs/Color"}},
                   "$defs": {"Color": {
                       "type": "object", "required": ["r"], "additionalProperties": False,
                       "properties": {"r": {"type": "integer", "minimum": 0, "maximum": 255}},
                   }}},
    }
    proposal = valid_proposal()
    proposal["commands"][0].update(action="set_color", params={"color": {"r": 128}})
    app.state.llm_client.propose.return_value = json.dumps(proposal)
    assert client.post("/simulation/propose", json={"model": "local-model", "prompt": "Rouge"}).status_code == 200
    proposal["commands"][0]["params"]["color"]["r"] = 999
    app.state.llm_client.propose.return_value = json.dumps(proposal)
    assert client.post("/simulation/propose", json={"model": "local-model", "prompt": "Rouge"}).status_code == 502


@pytest.mark.parametrize("invalid_inventory", ["not_simulation", "duplicate_device", "unknown_room", "reference"])
def test_invalid_inventory_blocks_inference(api, context, invalid_inventory):
    client, app, _ = api
    if invalid_inventory == "not_simulation":
        context["simulation"] = False
    elif invalid_inventory == "duplicate_device":
        context["devices"].append(deepcopy(context["devices"][0]))
    elif invalid_inventory == "unknown_room":
        context["devices"][0]["room_id"] = "missing"
    else:
        context["devices"][0]["actions"][0]["params"]["$ref"] = "http://other-host/schema"
    response = client.post("/simulation/propose", json={"model": "local-model", "prompt": "Éclaire"})
    assert response.status_code == 503
    app.state.llm_client.propose.assert_not_called()


def test_unavailable_simulator_and_model_backend_report_errors(api):
    client, app, _ = api
    app.state.llm_client.propose.side_effect = LLMClientError("private upstream details")
    response = client.post("/simulation/propose", json={"model": "local-model", "prompt": "Éclaire"})
    assert response.status_code == 502
    assert response.json()["detail"] == "The model backend is unavailable."
    assert "private upstream details" not in response.text

    def timeout(request):
        raise httpx.ReadTimeout("Simulator offline", request=request)

    app.state.simulation_client = SimulationClient("http://configured-simulation", transport=httpx.MockTransport(timeout))
    app.state.llm_client.propose.reset_mock()
    assert client.get("/simulation/home").status_code == 503
    assert client.post("/simulation/propose", json={"model": "local-model", "prompt": "Éclaire"}).status_code == 503
    app.state.llm_client.propose.assert_not_called()


@pytest.mark.parametrize("url", ["", "file:///etc/passwd", "http://localhost:invalid", "http://user:pass@localhost"])
def test_missing_or_invalid_server_configuration_is_unavailable(api, url):
    client, app, _ = api
    app.state.simulation_client = SimulationClient(url)
    assert client.get("/simulation/home").status_code == 503


def test_client_cannot_supply_a_simulator_destination(api):
    client, app, requests = api
    response = client.post("/simulation/propose", json={
        "model": "local-model", "prompt": "Éclaire", "simulation_url": "http://other-host",
    })
    assert response.status_code == 422
    assert requests == []
    app.state.llm_client.propose.assert_not_called()


def test_simulation_url_setting_comes_from_environment(monkeypatch):
    monkeypatch.setenv("JABFY_SIMULATION_URL", "http://configured-home:8090")
    get_settings.cache_clear()
    try:
        assert get_settings().simulation_url == "http://configured-home:8090"
    finally:
        get_settings.cache_clear()


def test_legacy_act_contract_keeps_its_existing_orchestrator(api):
    client, app, requests = api
    app.state.action_orchestrator = Mock()
    app.state.action_orchestrator.act.return_value = ActionResponse(
        action_chain="Allumer l’entrée.", changes={"hallway_light": True},
        verification=VerificationDecision(
            allowed=True, reason="Valid legacy action.", safe_changes={"hallway_light": True},
        ),
    )
    response = client.post("/act", json={
        "model": "local-model", "prompt": "Allume l’entrée", "device_state": {"hallway_light": False},
    })
    assert response.status_code == 200
    assert response.json()["changes"] == {"hallway_light": True}
    assert response.json()["verification"]["safe_changes"] == {"hallway_light": True}
    assert "commands" not in response.json()
    assert requests == []
