from fastapi import APIRouter, Request

from app.schemas.models import ModelsResponse

router = APIRouter(tags=["models"])


@router.get("/models", response_model=ModelsResponse)
def get_models(request: Request) -> ModelsResponse:
    try:
        models = request.app.state.llm_client.list_models()
        return ModelsResponse(models=models, available=True)
    except Exception as exc:
        return ModelsResponse(
            models=[],
            available=False,
            reason=f"The model backend is unavailable: {exc}",
        )
