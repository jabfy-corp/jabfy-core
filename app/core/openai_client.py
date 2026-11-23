from typing import Any

import httpx

from app.core.errors import LLMClientError
from app.schemas.generation import GenerationParams


class OpenAICompatibleClient:
    """Client for any OpenAI-compatible chat API.

    Covers a local llama.cpp server (``http://localhost:8080/v1``, no key) and
    hosted providers (``https://.../v1`` with a bearer key).

    Raises :exc:`LLMClientError` for any network or protocol failure so callers
    do not need to import ``httpx`` to handle errors.

    Args:
        transport: Optional ``httpx.BaseTransport`` injected for testing.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(headers=headers, timeout=timeout, transport=transport)

    # ------------------------------------------------------------------
    # LLMClient protocol

    def list_models(self) -> list[str]:
        try:
            response = self._client.get(f"{self._base_url}/models")
            response.raise_for_status()
            entries: Any = response.json().get("data", [])
            return [str(e["id"]) for e in entries if isinstance(e, dict) and e.get("id")]
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise LLMClientError(f"Failed to list models: {exc}") from exc

    def propose(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        params: GenerationParams | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
        }
        payload.update((params or GenerationParams()).to_payload())
        if response_schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "jabfy_proposal", "schema": response_schema},
            }

        try:
            response = self._client.post(
                f"{self._base_url}/chat/completions", json=payload
            )
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise LLMClientError(f"chat/completions request failed: {exc}") from exc

        # Some OpenAI-compatible servers (llama.cpp) return HTTP 200 with an
        # {"error": ...} body instead of a 4xx/5xx status.
        if "error" in body:
            raise LLMClientError(f"Backend returned an error: {body['error']}")

        choices = body.get("choices", [])
        if not choices:
            return ""
        return str(choices[0].get("message", {}).get("content", ""))

    def close(self) -> None:
        self._client.close()
