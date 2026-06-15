import pytest

from app.core.action_parser import ActionParseError, parse_action_proposal


def test_extracts_json_from_markdown_fence() -> None:
    proposal = parse_action_proposal(
        """```json
        {"action_chain":"Turn on the light","changes":{"hallway_light":true}}
        ```"""
    )

    assert proposal.action_chain == "Turn on the light"
    assert proposal.changes == {"hallway_light": True}


def test_extracts_json_surrounded_by_text() -> None:
    proposal = parse_action_proposal(
        'Proposal: {"action_chain":"No change","changes":{}} Done.'
    )

    assert proposal.changes == {}


def test_rejects_response_without_json() -> None:
    with pytest.raises(ActionParseError):
        parse_action_proposal("Turn on the hallway light.")
