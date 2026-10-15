"""jabfy-guard is the only gate of Core's bus: real BusRuntime, only MQTT is faked."""

from unittest.mock import patch

from jabfy_bus.config import load_config
from jabfy_bus.core.message import Entity, new_message
from jabfy_bus.core.types import MessageType, TrustLevel

from app.core.bus_runtime import BusRuntime
from app.core.config import DEFAULT_BUS_CONFIG
from app.core.guard import MAX_PER_MINUTE, SOURCE
from app.schemas.simulation import SimulationContext

NO_PARAMS = {"type": "object", "properties": {}, "additionalProperties": False}
TEMPERATURE = {"type": "object", "additionalProperties": False, "required": ["temperature"],
               "properties": {"temperature": {"type": "number", "minimum": 5, "maximum": 35}}}


def device(device_id, domain, suffix, actions):
    wire = f"sim_maison_{device_id}"
    return {
        "id": device_id, "name": device_id, "type": domain, "room_id": "salon",
        "room_name": "Salon", "state": {}, "sensor_events": [],
        "actions": [{"action": action, "label": action, "params": params}
                    for action, params in actions.items()],
        "bus": {"entity_id": f"{domain}.{wire}_{suffix}", "domain": domain,
                "topic": f"zigbee2mqtt/{wire}"},
    }


def home_context():
    return SimulationContext.model_validate({
        "schema_version": 1, "simulation": True, "revision": "r1", "status": "running",
        "home": {"id": "maison", "name": "Maison", "rooms": [{"id": "salon", "name": "Salon"}]},
        "devices": [
            device("lamp", "switch", "state", {"turn_on": NO_PARAMS, "turn_off": NO_PARAMS}),
            device("thermostat", "climate", "setpoint", {"set_temperature": TEMPERATURE}),
            device("door", "lock", "state", {"lock": NO_PARAMS, "unlock": NO_PARAMS}),
        ],
    })


def runtime():
    bus = BusRuntime(load_config(DEFAULT_BUS_CONFIG).policies)
    bus.sent = []
    bus.execution.register_transport("zigbee", lambda target, payload: bus.sent.append(target))
    return bus


def request(bus, device_id, domain, suffix, action, params=None, *, adapter=SOURCE, target=None):
    wire = f"sim_maison_{device_id}"
    bus.bus.publish(new_message(
        MessageType.COMMAND_REQUESTED, adapter=adapter, protocol="internal",
        trust_level=TrustLevel.INTERNAL,
        entity=Entity(id=f"{domain}.{wire}_{suffix}", domain=domain, location="salon"),
        command={"action": action, "params": params or {}, "protocol": "zigbee",
                 "target": target or f"zigbee2mqtt/{wire}"},
    ))
    return bus.verification.decisions[-1]


def test_commands_are_rejected_until_the_inventory_is_loaded():
    bus = runtime()
    assert request(bus, "lamp", "switch", "state", "turn_on").policy == "guard:UNTRUSTED_TARGET"
    bus.register_inventory(home_context())
    decision = request(bus, "lamp", "switch", "state", "turn_on")
    assert (decision.status, decision.policy) == ("approved", "guard:ALLOWED")
    assert "core_lights_v1" in decision.reason
    assert bus.sent == ["zigbee2mqtt/sim_maison_lamp/set"]


def test_core_policies_are_enforced_by_guard():
    bus = runtime()
    bus.register_inventory(home_context())
    decision = request(bus, "thermostat", "climate", "setpoint", "set_temperature",
                       {"temperature": 22})
    assert decision.approved and "core_thermostat_v1" in decision.reason
    assert request(bus, "thermostat", "climate", "setpoint", "set_temperature",
                   {"temperature": 80}).policy == "guard:INVALID_PARAMETERS"
    for action in ("lock", "unlock"):
        assert request(bus, "door", "lock", "state", action).policy == "guard:SENSITIVE_ACTION_BLOCKED"
    assert len(bus.sent) == 1


def test_only_core_may_command_inventory_targets():
    bus = runtime()
    bus.register_inventory(home_context())
    assert request(bus, "lamp", "switch", "state", "turn_on",
                   adapter="test").policy == "guard:UNTRUSTED_TARGET"
    assert request(bus, "lamp", "switch", "state", "turn_on",
                   target="zigbee2mqtt/other").policy == "guard:UNTRUSTED_TARGET"
    assert bus.sent == []


def test_rate_limit_per_policy():
    bus = runtime()
    bus.register_inventory(home_context())
    with patch("app.core.guard.time.time", return_value=1000.0):
        for _ in range(MAX_PER_MINUTE):
            assert request(bus, "lamp", "switch", "state", "turn_on").approved
        assert request(bus, "lamp", "switch", "state", "turn_on").policy == "guard:RATE_LIMIT"
    with patch("app.core.guard.time.time", return_value=1060.0):
        assert request(bus, "lamp", "switch", "state", "turn_on").approved
