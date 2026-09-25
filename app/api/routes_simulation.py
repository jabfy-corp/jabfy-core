"""Read-only discovery and validated action proposals for the configured simulation."""

from fastapi import APIRouter, HTTPException, Request

from app.schemas.simulation import ProposalRequest, SimulationContext, SimulationProposal
from app.simulation.client import SimulationUnavailable
from app.simulation.planner import InvalidSimulationProposal, propose

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
        return propose(payload, context, request.app.state.ollama_client)
    except SimulationUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except InvalidSimulationProposal as exc:
        raise HTTPException(502, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, "Ollama could not produce a simulation proposal.") from exc
