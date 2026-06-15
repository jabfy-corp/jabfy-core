from typing import Any

import ollama


class OllamaClient:
    def __init__(self, host: str) -> None:
        self._client = ollama.Client(host=host)

    def list_models(self) -> list[str]:
        response = self._client.list()
        models = getattr(response, "models", None)
        if models is None and isinstance(response, dict):
            models = response.get("models", [])

        names: list[str] = []
        for model in models or []:
            name = getattr(model, "model", None)
            if name is None and isinstance(model, dict):
                name = model.get("model") or model.get("name")
            if name:
                names.append(str(name))
        return names

    def propose(self, model: str, system_prompt: str, user_message: str) -> str:
        response: Any = self._client.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        message = getattr(response, "message", None)
        if message is not None:
            return str(getattr(message, "content", ""))
        if isinstance(response, dict):
            return str(response.get("message", {}).get("content", ""))
        return ""
