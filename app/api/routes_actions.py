from fastapi import APIRouter, HTTPException, Request

from app.schemas.actions import ActionRequest, ActionResponse

router = APIRouter(tags=["actions"])


@router.post("/act", response_model=ActionResponse)
def act(payload: ActionRequest, request: Request) -> ActionResponse:
    try:
        return request.app.state.action_orchestrator.act(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ollama request failed: {exc}") from exc
