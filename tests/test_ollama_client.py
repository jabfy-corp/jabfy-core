"""Structured output is opt-in; deterministic proposal validation remains separate."""

from unittest.mock import Mock, patch

from app.core.ollama_client import OllamaClient


def test_simulation_schema_is_passed_to_ollama():
    transport = Mock()
    transport.chat.return_value = {"message": {"content": '{"commands":[]}'}}
    schema = {"type": "object", "required": ["explanation", "commands"]}
    with patch("app.core.ollama_client.ollama.Client", return_value=transport):
        client = OllamaClient("http://ollama:11434")
        result = client.propose("local-model", "system", "user", response_schema=schema)
    assert result == '{"commands":[]}'  # Parsing/validation belongs to the planner.
    assert transport.chat.call_args.kwargs["format"] == schema
    assert transport.chat.call_args.kwargs["options"] == {"temperature": 0}


def test_legacy_proposals_keep_their_original_request_format():
    transport = Mock()
    transport.chat.return_value = {"message": {"content": "legacy response"}}
    with patch("app.core.ollama_client.ollama.Client", return_value=transport):
        client = OllamaClient("http://ollama:11434")
        assert client.propose("local-model", "system", "user") == "legacy response"
    assert "format" not in transport.chat.call_args.kwargs
    assert "options" not in transport.chat.call_args.kwargs
