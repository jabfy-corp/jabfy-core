import json

import httpx
import pytest

from app.core.errors import LLMClientError
from app.core.openai_client import OpenAICompatibleClient
from app.schemas.generation import GenerationParams


def build_client(
    handler,
    api_key: str | None = None,
    timeout: float = 5.0,
) -> OpenAICompatibleClient:
    """Build a client that routes all requests through *handler* via MockTransport."""
    return OpenAICompatibleClient(
        base_url="http://llm.test/v1",
        api_key=api_key,
        timeout=timeout,
        transport=httpx.MockTransport(handler),
    )


def test_lists_models_from_openai_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://llm.test/v1/models"
        return httpx.Response(200, json={"data": [{"id": "qwen3"}, {"id": "gemma3"}]})

    assert build_client(handler).list_models() == ["qwen3", "gemma3"]


def test_propose_forwards_sampling_parameters() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"action_chain":"ok","changes":{}}'}}]},
        )

    content = build_client(handler).propose(
        model="qwen3",
        system_prompt="system",
        user_message="user",
        params=GenerationParams(temperature=0.2, top_k=20, n_predict=64),
    )

    assert content == '{"action_chain":"ok","changes":{}}'
    assert captured["model"] == "qwen3"
    assert captured["stream"] is False
    assert captured["messages"][0] == {"role": "system", "content": "system"}
    assert captured["temperature"] == 0.2
    assert captured["top_k"] == 20
    assert captured["max_tokens"] == 64
    assert "top_p" not in captured


def test_propose_without_params_sends_no_sampling_keys() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "hi"}}]})

    build_client(handler).propose("qwen3", "system", "user")

    assert set(captured) == {"model", "messages", "stream"}


def test_propose_forwards_optional_schema_without_changing_legacy_calls() -> None:
    captured = {}
    schema = {"type": "object", "required": ["explanation", "commands"]}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={
            "choices": [{"message": {"content": '{"explanation":"ok","commands":[]}'}}],
        })

    client = build_client(handler)
    try:
        result = client.propose(
            "local-model", "system", "user",
            params=GenerationParams(temperature=0), response_schema=schema,
        )
    finally:
        client.close()
    assert json.loads(result)["commands"] == []
    assert captured["response_format"] == {
        "type": "json_schema", "json_schema": {"name": "jabfy_proposal", "schema": schema},
    }
    assert captured["temperature"] == 0


def test_propose_returns_empty_string_without_choices() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": []})

    assert build_client(handler).propose("qwen3", "system", "user") == ""


def test_sends_bearer_key_when_configured() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"data": []})

    build_client(handler, api_key="sk-test").list_models()

    assert seen["auth"] == "Bearer sk-test"


def test_sends_no_auth_header_without_key() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"data": []})

    build_client(handler).list_models()

    assert seen["auth"] is None


def test_propose_raises_llm_client_error_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    with pytest.raises(LLMClientError):
        build_client(handler).propose("qwen3", "system", "user")


def test_list_models_raises_llm_client_error_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Service Unavailable")

    with pytest.raises(LLMClientError):
        build_client(handler).list_models()


def test_propose_raises_on_error_body() -> None:
    """llama.cpp-style: HTTP 200 but body contains {"error": ...}."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"error": {"message": "model not found"}})

    with pytest.raises(LLMClientError, match="Backend returned an error"):
        build_client(handler).propose("missing-model", "system", "user")


def test_close_shuts_down_httpx_client() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        return httpx.Response(200, json={"data": []})

    client = build_client(handler)
    client.close()  # must not raise
    assert client._client.is_closed
