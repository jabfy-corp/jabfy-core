"""Bus participant (MASTER_PLAN §2.2): situations in, command.requested out.

A single worker consumes a bounded queue, so runs never interleave. The model
only proposes; every command still crosses the VerificationEngine.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Callable
from uuid import uuid4

from jabfy_bus.core.message import BusMessage, Entity, Value, new_message
from jabfy_bus.core.types import MessageType, TrustLevel

from app.core.bus_runtime import BusRuntime
from app.core.errors import LLMClientError
from app.core.llm_client import LLMClient
from app.core.run_journal import RunJournal
from app.schemas.simulation import ProposalRequest, SimulationContext
from app.simulation.client import SimulationUnavailable
from app.simulation.planner import InvalidSimulationProposal, propose

logger = logging.getLogger(__name__)

ADAPTER = "core_orchestrator"
SENSOR_DOMAIN = "binary_sensor"


@dataclass(frozen=True)
class Job:
    run_id: str
    model: str
    message: str


class ActionOrchestrator:
    def __init__(
        self,
        runtime: BusRuntime,
        journal: RunJournal,
        *,
        fetch_context: Callable[[], SimulationContext],
        llm_client: Callable[[], LLMClient],
        llm_timeout: float,
        headless_model: str = "",
        cooldown: float = 30.0,
        queue_size: int = 16,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._runtime = runtime
        self._journal = journal
        self._fetch_context = fetch_context
        self._llm_client = llm_client
        self._llm_timeout = llm_timeout
        self._headless_model = headless_model
        self._cooldown = cooldown
        self._queue_size = queue_size
        self._clock = clock
        self._queue: asyncio.Queue[Job] | None = None
        self._worker_task: asyncio.Task | None = None
        self._sensor_values: dict[str, object] = {}
        self._sensor_runs: dict[str, float] = {}

    @property
    def bus(self):
        return self._runtime.bus

    def attach(self) -> None:
        for pattern in (MessageType.USER_SITUATION.value, MessageType.TELEMETRY.value,
                        MessageType.STATE_CHANGED.value):
            self.bus.subscribe(pattern, self.on_event, name="action_orchestrator")

    def start(self) -> None:
        self._queue = asyncio.Queue(maxsize=self._queue_size)
        self._worker_task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        if self._worker_task is not None:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    def full(self) -> bool:
        return self._queue is None or self._queue.full()

    def on_event(self, message: BusMessage) -> None:
        if message.message_type == MessageType.USER_SITUATION.value:
            model, prompt = message.raw.get("model"), message.raw.get("prompt")
            self._journal.create(message.message_id, source="prompt", model=model, request=prompt)
            self._enqueue(Job(message.message_id, model, prompt))
        elif message.entity is not None and message.entity.domain == SENSOR_DOMAIN:
            self._on_sensor(message)

    def _on_sensor(self, message: BusMessage) -> None:
        entity = message.entity
        value = message.value.normalized if message.value else None
        previous = self._sensor_values.get(entity.id)
        self._sensor_values[entity.id] = value
        if previous is None or previous == value or not self._headless_model:
            return
        now = self._clock()
        last = self._sensor_runs.get(entity.id)
        if last is not None and now - last < self._cooldown:
            return
        self._sensor_runs[entity.id] = now
        situation = {
            "trigger": "sensor", "entity_id": entity.id, "class": entity.entity_class,
            "room": entity.location, "previous": previous, "value": value,
            "time": message.timestamp,
        }
        run_id = str(uuid4())
        self._journal.create(run_id, source="sensor", model=self._headless_model, request=situation)
        self._enqueue(Job(run_id, self._headless_model, json.dumps(situation, ensure_ascii=False)))

    def _enqueue(self, job: Job) -> None:
        try:
            self._queue.put_nowait(job)
        except (AttributeError, asyncio.QueueFull):
            self._journal.update(job.run_id, status="failed", error="The reasoning queue is full.")

    async def _worker(self) -> None:
        while True:
            job = await self._queue.get()
            try:
                await self._run(job)
            except Exception:
                logger.exception("run %s crashed", job.run_id)
                self._journal.update(job.run_id, status="failed", error="Internal error.")

    async def _run(self, job: Job) -> None:
        self._journal.update(job.run_id, status="planning")
        try:
            context = await asyncio.to_thread(self._fetch_context)
            self._runtime.register_inventory(context)
            proposal = await asyncio.wait_for(
                asyncio.to_thread(
                    propose, ProposalRequest(model=job.model, prompt=job.message),
                    context, self._llm_client(),
                ),
                timeout=self._llm_timeout,
            )
        except (SimulationUnavailable, InvalidSimulationProposal) as exc:
            self._journal.update(job.run_id, status="failed", error=str(exc))
            return
        except (LLMClientError, TimeoutError):
            self._journal.update(job.run_id, status="failed",
                                 error="The model backend is unavailable.")
            return

        self._publish_reasoning(job, proposal.explanation, len(proposal.commands))
        if not proposal.commands:
            self._journal.update(job.run_id, status="no_action")
            return

        self._journal.update(job.run_id, status="running")
        devices = {device.id: device for device in context.devices}
        for command in proposal.commands:
            await asyncio.sleep(command.delay_ms / 1000)
            device = devices[command.device_id]
            summary = {"device_id": command.device_id, "action": command.action,
                       "params": command.params, "delay_ms": command.delay_ms}
            if device.bus is None:
                step = self._journal.add_step(job.run_id, str(uuid4()), summary)
                step.update(status="failed", reason="The device has no bus address.")
                self._journal.update(job.run_id, status="failed", error=step["reason"])
                return
            request = new_message(
                MessageType.COMMAND_REQUESTED, adapter=ADAPTER, protocol="internal",
                trust_level=TrustLevel.INTERNAL, correlation_id=job.run_id,
                entity=Entity(id=device.bus.entity_id, domain=device.bus.domain,
                              location=device.room_id),
                command={"action": command.action, "params": command.params,
                         "protocol": "zigbee", "target": device.bus.topic},
                raw={"run_id": job.run_id, "device_id": device.id},
            )
            step = self._journal.add_step(job.run_id, request.message_id, summary)
            self.bus.publish(request)
            if step["status"] != "executed":
                status = "rejected" if step["status"] == "rejected" else "failed"
                self._journal.update(job.run_id, status=status,
                                     error=step["reason"] or "The bus did not confirm execution.")
                return
        self._journal.update(job.run_id, status="completed")

    def _publish_reasoning(self, job: Job, explanation: str, count: int) -> None:
        self.bus.publish(new_message(
            MessageType.EVENT, adapter=ADAPTER, protocol="internal",
            trust_level=TrustLevel.INTERNAL, correlation_id=job.run_id,
            entity=Entity(id="automation.core_reasoning", domain="automation",
                          name="Jabfy Core reasoning"),
            value=Value(raw=explanation, normalized=explanation, datatype="str"),
            raw={"kind": "reasoning", "run_id": job.run_id, "explanation": explanation,
                 "commands": count},
        ))
