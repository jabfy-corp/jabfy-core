import logging

from fastapi import APIRouter, Request

from app.core.errors import LLMClientError
from app.schemas.models import ModelsResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["models"])


@router.get("/models", response_model=ModelsResponse)
def get_models(request: Request) -> ModelsResponse:
    try:
        models = request.app.state.llm_client.list_models()
        return ModelsResponse(models=models, available=True)
    except LLMClientError as exc:
        logger.warning("LLM backend unavailable", exc_info=exc)
        return ModelsResponse(
            models=[],
            available=False,
            reason="The model backend is unavailable.",
        )
