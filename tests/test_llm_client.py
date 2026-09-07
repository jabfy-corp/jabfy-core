from app.core.config import Settings
from app.core.llm_client import build_llm_client
from app.core.openai_client import OpenAICompatibleClient


def test_builds_an_openai_compatible_client() -> None:
    assert isinstance(build_llm_client(Settings()), OpenAICompatibleClient)


def test_defaults_to_a_local_llama_cpp_server() -> None:
    settings = Settings()

    assert settings.llm_base_url == "http://localhost:8080/v1"
    assert settings.llm_api_key is None
