from typing import Protocol

from app.core.config import Settings
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
    ) -> str: ...


def build_llm_client(settings: Settings) -> LLMClient:
    return OpenAICompatibleClient(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
    )
