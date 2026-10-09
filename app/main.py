from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_actions import router as actions_router
from app.api.routes_health import router as health_router
from app.api.routes_models import router as models_router
from app.api.routes_simulation import router as simulation_router
from app.core.action_orchestrator import ActionOrchestrator
from app.core.config import get_settings
from app.simulation.client import SimulationClient
from app.core.llm_client import build_llm_client


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        yield
        application.state.llm_client.close()

    application = FastAPI(
        title="JABFY Core",
        version="0.1.0",
        description="Local-first Smart Home orchestration API.",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )

    llm_client = build_llm_client(settings)
    application.state.llm_client = llm_client
    application.state.action_orchestrator = ActionOrchestrator(llm_client)
    application.state.simulation_client = SimulationClient(settings.simulation_url)

    application.include_router(health_router)
    application.include_router(models_router)
    application.include_router(actions_router)
    application.include_router(simulation_router)
    return application


app = create_app()
