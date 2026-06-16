import json
import re
from collections.abc import Mapping

from app.schemas.actions import ActionProposal


class ActionParseError(ValueError):
    pass


def _strip_code_fence(content: str) -> str:
    stripped = content.strip()
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
    return re.sub(r"\s*```$", "", stripped).strip()


def parse_action_proposal(content: str) -> ActionProposal:
    cleaned = _strip_code_fence(content)
    decoder = json.JSONDecoder()

    for index, character in enumerate(cleaned):
        if character != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, Mapping):
            continue

        action_chain = payload.get("action_chain", "Action proposed.")
        changes = payload.get("changes", {})
        if not isinstance(action_chain, str):
            raise ActionParseError('"action_chain" must be a string.')
        if not isinstance(changes, Mapping):
            raise ActionParseError('"changes" must be an object.')
        return ActionProposal(action_chain=action_chain, changes=dict(changes))

    raise ActionParseError("No valid JSON object found in the model response.")
