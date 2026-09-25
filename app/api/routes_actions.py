import logging

from fastapi import APIRouter, HTTPException, Request

from app.core.errors import LLMClientError
from app.schemas.actions import ActionRequest, ActionResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["actions"])


@router.post("/act", response_model=ActionResponse)
def act(payload: ActionRequest, request: Request) -> ActionResponse:
    try:
        return request.app.state.action_orchestrator.act(payload)
    except LLMClientError as exc:
        logger.warning("LLM backend call failed", exc_info=exc)
        raise HTTPException(status_code=502, detail="The model backend is unavailable.") from exc
