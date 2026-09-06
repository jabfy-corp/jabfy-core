from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_actions import router as actions_router
from app.api.routes_health import router as health_router
from app.api.routes_models import router as models_router
from app.core.action_orchestrator import ActionOrchestrator
from app.core.config import get_settings
from app.core.llm_client import build_llm_client


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="JABFY Core",
        version="0.1.0",
        description="Local-first Smart Home orchestration API.",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    llm_client = build_llm_client(settings)
    application.state.llm_client = llm_client
    application.state.action_orchestrator = ActionOrchestrator(llm_client)

    application.include_router(health_router)
    application.include_router(models_router)
    application.include_router(actions_router)
    return application


app = create_app()
