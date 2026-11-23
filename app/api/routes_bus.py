"""Headless entry points (MASTER_PLAN §2.4): a prompt becomes a bus situation."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from jabfy_bus.core.message import new_message
from jabfy_bus.core.types import MessageType, TrustLevel

from app.schemas.simulation import ProposalRequest

router = APIRouter(tags=["bus"])


@router.post("/prompt", status_code=202)
async def prompt(payload: ProposalRequest, request: Request) -> dict[str, str]:
    if request.app.state.action_orchestrator.full():
        raise HTTPException(429, "Too many runs in progress.")
    situation = new_message(
        MessageType.USER_SITUATION, adapter="core_api", protocol="http",
        trust_level=TrustLevel.INTERNAL,
        raw={"prompt": payload.prompt, "model": payload.model},
    )
    request.app.state.bus_runtime.bus.publish(situation)
    return {"prompt_id": situation.message_id}


@router.get("/prompts/{prompt_id}")
async def prompt_run(prompt_id: str, request: Request) -> dict[str, Any]:
    run = request.app.state.run_journal.get(prompt_id)
    if run is None:
        raise HTTPException(404, "Unknown prompt.")
    return run


@router.get("/state")
async def state(request: Request) -> dict[str, Any]:
    runtime = request.app.state.bus_runtime
    return {
        "mqtt_connected": runtime.connected,
        "entities": [
            {"id": record.entity_id, "domain": record.domain, "class": record.entity_class,
             "location": record.location, "last_value": record.last_value,
             "last_seen": record.last_seen}
            for record in runtime.registry.list()
        ],
    }


@router.get("/audit/verify")
async def audit_verify(request: Request) -> dict[str, Any]:
    audit = request.app.state.bus_runtime.audit
    return {"verified": audit.verify(), "records": len(audit)}
