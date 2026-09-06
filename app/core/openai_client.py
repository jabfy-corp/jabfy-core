from typing import Any

import httpx

from app.schemas.generation import GenerationParams


class OpenAICompatibleClient:
    """Client for any OpenAI-compatible chat API.

    Covers a local llama.cpp server (`http://localhost:8080/v1`, no key) and
    hosted providers (`https://.../v1` with a bearer key).
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(headers=headers, timeout=timeout)

    def list_models(self) -> list[str]:
        response = self._client.get(f"{self._base_url}/models")
        response.raise_for_status()
        entries: Any = response.json().get("data", [])
        return [str(entry["id"]) for entry in entries if entry.get("id")]

    def propose(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        params: GenerationParams | None = None,
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

        response = self._client.post(
            f"{self._base_url}/chat/completions", json=payload
        )
        response.raise_for_status()
        choices = response.json().get("choices", [])
        if not choices:
            return ""
        return str(choices[0].get("message", {}).get("content", ""))
