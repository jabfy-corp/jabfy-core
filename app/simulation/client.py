"""Read a configured simulator catalog; never accept an upstream URL from a request."""

import json
from urllib.parse import urlsplit

import httpx
from pydantic import ValidationError

from app.schemas.simulation import SimulationContext


class SimulationUnavailable(Exception):
    pass


class SimulationClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.strip().rstrip("/")
        self.timeout = timeout
        self.transport = transport

    def fetch_context(self) -> SimulationContext:
        try:
            parsed = urlsplit(self.base_url)
            _ = parsed.port
            if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                    or parsed.username or parsed.password or parsed.query or parsed.fragment):
                raise ValueError("Invalid simulator URL")
        except ValueError as exc:
            raise SimulationUnavailable("JABFY_SIMULATION_URL is missing or invalid.") from exc

        try:
            with httpx.Client(
                timeout=self.timeout, transport=self.transport, follow_redirects=False,
            ) as client:
                response = client.get(f"{self.base_url}/api/ai/context")
                response.raise_for_status()
                data = response.json()
                json.dumps(data, allow_nan=False)
                return SimulationContext.model_validate(data)
        except (httpx.HTTPError, httpx.InvalidURL) as exc:
            raise SimulationUnavailable("The configured simulator is unavailable.") from exc
        except (ValueError, ValidationError) as exc:
            raise SimulationUnavailable("The simulator returned an invalid home inventory.") from exc
