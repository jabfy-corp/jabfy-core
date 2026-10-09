from typing import Any, Protocol

from app.core.config import Settings
from app.core.errors import LLMClientError  # noqa: F401 — re-exported for callers
from app.core.openai_client import OpenAICompatibleClient
from app.schemas.generation import GenerationParams


class LLMClient(Protocol):
    def list_models(self) -> list[str]: ...

    def propose(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        params: GenerationParams | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> str: ...

    def close(self) -> None: ...


def build_llm_client(settings: Settings) -> LLMClient:
    match settings.llm_provider:
        case "openai_compat":
            return OpenAICompatibleClient(
                base_url=settings.llm_base_url,
                api_key=settings.llm_api_key,
                timeout=settings.llm_timeout,
            )
        case _:
            raise ValueError(
                f"Unknown LLM provider: {settings.llm_provider!r}. "
                "Set JABFY_LLM_PROVIDER to a supported value (e.g. 'openai_compat')."
            )
