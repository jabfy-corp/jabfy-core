"""Read-only discovery and validated action proposals for the configured simulation."""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.core.errors import LLMClientError
from app.schemas.simulation import ProposalRequest, SimulationContext, SimulationProposal
from app.simulation.client import SimulationUnavailable
from app.simulation.planner import InvalidSimulationProposal, propose

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.get("/home", response_model=SimulationContext)
def home(request: Request) -> SimulationContext:
    try:
        return request.app.state.simulation_client.fetch_context()
    except SimulationUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


@router.post("/propose", response_model=SimulationProposal)
def propose_simulation(payload: ProposalRequest, request: Request) -> SimulationProposal:
    try:
        context = request.app.state.simulation_client.fetch_context()
        return propose(payload, context, request.app.state.llm_client)
    except SimulationUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except InvalidSimulationProposal as exc:
        raise HTTPException(502, str(exc)) from exc
    except LLMClientError as exc:
        logger.warning("LLM backend call failed", exc_info=exc)
        raise HTTPException(502, "The model backend is unavailable.") from exc
