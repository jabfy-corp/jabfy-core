import pytest

from app.core.config import Settings
from app.core.llm_client import build_llm_client
from app.core.openai_client import OpenAICompatibleClient


def test_builds_openai_compat_client_by_default() -> None:
    client = build_llm_client(Settings())
    assert isinstance(client, OpenAICompatibleClient)
    client.close()


def test_openai_compat_client_uses_configured_base_url() -> None:
    settings = Settings(llm_provider="openai_compat", llm_base_url="http://llm.test/v1")
    client = build_llm_client(settings)
    assert isinstance(client, OpenAICompatibleClient)
    assert client._base_url == "http://llm.test/v1"
    client.close()


def test_timeout_is_forwarded_to_client() -> None:
    settings = Settings(llm_timeout=30.0)
    client = build_llm_client(settings)
    assert isinstance(client, OpenAICompatibleClient)
    assert client._client.timeout.read == pytest.approx(30.0)
    client.close()


def test_unknown_provider_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        build_llm_client(Settings(llm_provider="unknown_provider"))


def test_defaults_to_local_llama_cpp_server() -> None:
    settings = Settings()
    assert settings.llm_base_url == "http://localhost:8080/v1"
    assert settings.llm_api_key is None
    assert settings.llm_timeout == 120.0
    assert settings.llm_provider == "openai_compat"
