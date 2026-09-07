import json

import httpx

from app.core.openai_client import OpenAICompatibleClient
from app.schemas.generation import GenerationParams


def build_client(handler, api_key: str | None = None) -> OpenAICompatibleClient:
    client = OpenAICompatibleClient(base_url="http://llm.test/v1", api_key=api_key)
    client._client = httpx.Client(
        headers=client._client.headers,
        transport=httpx.MockTransport(handler),
    )
    return client


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
