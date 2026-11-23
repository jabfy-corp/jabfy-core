"""Bounded per-run record built from bus messages.

The bus history is quickly overwritten by telemetry, so each run keeps its own
steps: requested -> approved | rejected -> executed | failed.
"""

from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from jabfy_bus.core.bus import UniversalJsonBus
from jabfy_bus.core.message import BusMessage

TERMINAL = {"completed", "failed", "rejected", "no_action"}
# The bus dispatches depth-first: approved/executed can reach us before requested.
STEP_RANK = {"pending": 0, "requested": 1, "approved": 2, "rejected": 3, "executed": 3, "failed": 3}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunJournal:
    def __init__(self, limit: int = 100) -> None:
        self._runs: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._steps: dict[str, dict[str, Any]] = {}
        self._limit = limit

    def attach(self, bus: UniversalJsonBus) -> None:
        bus.subscribe("command.*", self._on_command, name="run_journal")
        bus.subscribe("event", self._on_event, name="run_journal")

    def create(self, run_id: str, *, source: str, model: str, request: Any) -> dict[str, Any]:
        run = {
            "id": run_id, "source": source, "model": model, "request": request,
            "status": "queued", "explanation": None, "error": None, "steps": [],
            "created_at": _now(), "finished_at": None,
        }
        self._runs[run_id] = run
        while len(self._runs) > self._limit:
            _, dropped = self._runs.popitem(last=False)
            for step in dropped["steps"]:
                self._steps.pop(step["request_id"], None)
        return run

    def get(self, run_id: str) -> dict[str, Any] | None:
        run = self._runs.get(run_id)
        return deepcopy(run) if run is not None else None

    def status(self, run_id: str) -> str | None:
        run = self._runs.get(run_id)
        return run["status"] if run is not None else None

    def update(self, run_id: str, **fields: Any) -> None:
        run = self._runs.get(run_id)
        if run is None:
            return
        run.update(fields)
        if run["status"] in TERMINAL and run["finished_at"] is None:
            run["finished_at"] = _now()

    def add_step(self, run_id: str, request_id: str, command: dict[str, Any]) -> dict[str, Any]:
        step = {**command, "request_id": request_id, "status": "pending",
                "reason": None, "history": []}
        run = self._runs.get(run_id)
        if run is not None:
            run["steps"].append(step)
            self._steps[request_id] = step
        return step

    def _on_command(self, message: BusMessage) -> None:
        if message.message_type == "command.requested":
            step, status, reason = self._steps.get(message.message_id), "requested", None
        else:
            step = self._steps.get(message.correlation_id or "")
            if message.message_type == "command.executed":
                success = message.raw.get("success") is True
                status, reason = ("executed", None) if success else ("failed", message.raw.get("error"))
            else:
                status = message.message_type.removeprefix("command.")
                reason = message.raw.get("decision", {}).get("reason")
        if step is None:
            return
        if STEP_RANK[status] > STEP_RANK[step["status"]]:
            step["status"] = status
        step["reason"] = reason or step["reason"]
        step["history"].append({"status": status, "time": message.timestamp})
        step["history"].sort(key=lambda entry: STEP_RANK[entry["status"]])

    def _on_event(self, message: BusMessage) -> None:
        run = self._runs.get(message.raw.get("run_id", ""))
        if run is not None and message.raw.get("kind") == "reasoning":
            run["explanation"] = message.raw.get("explanation")
