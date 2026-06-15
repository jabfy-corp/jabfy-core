from app.core.action_parser import ActionParseError, parse_action_proposal
from app.core.ollama_client import OllamaClient
from app.core.prompt_builder import SYSTEM_PROMPT, build_user_message
from app.core.verification import verify_changes
from app.schemas.actions import (
    ActionRequest,
    ActionResponse,
    UniversalBusEvent,
    UserSituationPayload,
    VerificationDecision,
)


class ActionOrchestrator:
    def __init__(self, ollama_client: OllamaClient) -> None:
        self._ollama_client = ollama_client

    def act(self, request: ActionRequest) -> ActionResponse:
        event = UniversalBusEvent(
            source="smart_home_simulation",
            event_type="user_situation",
            payload=UserSituationPayload(
                prompt=request.prompt,
                device_state=request.device_state,
            ),
        )
        content = self._ollama_client.propose(
            model=request.model,
            system_prompt=SYSTEM_PROMPT,
            user_message=build_user_message(
                event.payload.prompt,
                event.payload.device_state,
            ),
        )

        try:
            proposal = parse_action_proposal(content)
        except ActionParseError as exc:
            verification = VerificationDecision(
                allowed=False,
                reason=str(exc),
                safe_changes={},
            )
            return ActionResponse(
                action_chain="The model response could not be parsed.",
                changes={},
                verification=verification,
            )

        verification = verify_changes(proposal.changes)
        return ActionResponse(
            action_chain=proposal.action_chain,
            changes=verification.safe_changes,
            verification=verification,
        )
