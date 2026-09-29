import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from jabfy_bus.api.ws import register_ws_routes
from jabfy_bus.config import load_config

from app.api.routes_bus import router as bus_router
from app.api.routes_health import router as health_router
from app.api.routes_models import router as models_router
from app.api.routes_simulation import router as simulation_router
from app.core.action_orchestrator import ActionOrchestrator
from app.core.bus_runtime import BusRuntime
from app.core.config import get_settings
from app.core.run_journal import RunJournal
from app.simulation.client import SimulationClient, SimulationUnavailable
from app.core.llm_client import build_llm_client

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        runtime = application.state.bus_runtime
        orchestrator = application.state.action_orchestrator
        runtime.start(asyncio.get_running_loop())
        orchestrator.start()
        try:
            runtime.register_inventory(
                await asyncio.to_thread(application.state.simulation_client.fetch_context)
            )
        except SimulationUnavailable:
            logger.warning("Simulation inventory not loaded at startup; retried on each run")
        yield
        await orchestrator.stop()
        runtime.stop()
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
    application.state.simulation_client = SimulationClient(settings.simulation_url)

    runtime = BusRuntime(load_config(settings.bus_config).policies, mqtt_broker=settings.mqtt_broker)
    journal = RunJournal()
    journal.attach(runtime.bus)
    orchestrator = ActionOrchestrator(
        runtime, journal,
        fetch_context=lambda: application.state.simulation_client.fetch_context(),
        llm_client=lambda: application.state.llm_client,
        llm_timeout=settings.llm_timeout,
        headless_model=settings.headless_model,
        cooldown=settings.headless_cooldown,
    )
    orchestrator.attach()
    application.state.bus_runtime = runtime
    application.state.run_journal = journal
    application.state.action_orchestrator = orchestrator

    application.include_router(health_router)
    application.include_router(models_router)
    application.include_router(simulation_router)
    application.include_router(bus_router)
    register_ws_routes(application, runtime.bus)
    return application


app = create_app()
