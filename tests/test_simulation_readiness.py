import httpx
import pytest

from app.simulation.client import SimulationClient, SimulationUnavailable


@pytest.mark.parametrize("status", ["starting", "error", "stopped"])
def test_inactive_simulation_is_not_used_for_proposals(status):
    inventory = {"schema_version": 1, "simulation": True, "status": status,
                 "revision": "v1", "home": {"id": "h", "name": "H", "rooms": []}, "devices": []}
    client = SimulationClient("http://sim.test", transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=inventory)))
    with pytest.raises(SimulationUnavailable, match="not running"):
        client.fetch_context()
