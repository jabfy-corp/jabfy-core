"""jabfy-guard authorizes every command of Core's bus (MASTER_PLAN §4: single verification pipeline).

Guard rules are built from the `config/bus.json` policies and the simulation inventory:
each policy covers the inventory devices of its domains, and a policy accepting high
risk allows sensitive actions on the virtual home. Critical actions are always denied.
"""

from collections import defaultdict, deque
import time

from jabfy_bus.core.message import BusMessage
from jabfy_bus.core.types import RiskLevel
from jabfy_bus.verification.policies import Policy as BusPolicy, PolicyDecision
from jabfy_guard import Capability, Context, Device, Parameter, Policy, PolicySet, evaluate

from app.schemas.simulation import SimulationContext

SOURCE = "core_orchestrator"
ROLE = "core"
MAX_PER_MINUTE = 60


def _parameters(schema, definitions=None):
    definitions = definitions or schema.get("$defs", {})
    if "$ref" in schema:
        schema = definitions[schema["$ref"].removeprefix("#/$defs/")]
    result = {}
    for name, value in schema.get("properties", {}).items():
        if "$ref" in value:
            value = definitions[value["$ref"].removeprefix("#/$defs/")]
        result[name] = Parameter(
            type=value["type"], required=name in schema.get("required", []),
            minimum=value.get("minimum"), maximum=value.get("maximum"),
            choices=value.get("enum"),
            properties=_parameters(value, definitions) if value["type"] == "object" else {},
        )
    return result


class CoreGuard:
    def __init__(self, policies: list[BusPolicy]) -> None:
        self.bus_policies = policies
        self.home_id = ""
        self.devices: dict[str, Device] = {}
        self.targets: dict[str, tuple[str, str]] = {}
        self.policies = PolicySet(version="core-empty", rules=[])
        self.counts: dict[str, deque] = defaultdict(deque)

    def load(self, context: SimulationContext) -> None:
        devices, targets = {}, {}
        for device in context.devices:
            if device.bus is not None:
                targets[device.bus.entity_id] = (device.id, device.bus.topic)
                devices[device.id] = Device(domain=device.bus.domain, actions={
                    item.action: Capability(parameters=_parameters(item.params))
                    for item in device.actions
                })
        rules = []
        for policy in self.bus_policies:
            covered = [device.id for device in context.devices if device.bus is not None
                       and (policy.domains is None or device.bus.domain in policy.domains)]
            actions = sorted(policy.actions or {a for d in covered for a in devices[d].actions})
            if covered and actions:
                rules.append(Policy(
                    id=policy.name, effect=policy.effect, home_id=context.home.id,
                    roles=[ROLE], devices=covered, actions=actions,
                    max_per_minute=MAX_PER_MINUTE,
                    allow_sensitive_simulation=policy.max_risk.rank() >= RiskLevel.HIGH.rank(),
                ))
        self.home_id, self.devices, self.targets = context.home.id, devices, targets
        self.policies = PolicySet(version=f"core-{context.revision}", rules=rules)

    def __call__(self, message: BusMessage) -> PolicyDecision:
        entity = message.entity.id if message.entity else None
        target = self.targets.get(entity)
        wire = message.command or {}
        if (message.source.adapter != SOURCE or target is None
                or wire.get("protocol") != "zigbee" or wire.get("target") != target[1]
                or set(wire) - {"action", "params", "protocol", "target"}):
            return PolicyDecision("rejected", "guard:UNTRUSTED_TARGET",
                                  "Source or target outside the simulation inventory.",
                                  RiskLevel.CRITICAL)
        now = time.time()
        counts = {}
        for rule in self.policies.rules:
            history = self.counts[rule.id]
            while history and history[0] <= now - 60:
                history.popleft()
            counts[rule.id] = len(history)
        context = Context(home_id=self.home_id, actor_id=SOURCE, roles=[ROLE], mode="normal",
                          simulation=True, observed_at=now, devices=self.devices,
                          recent_counts=counts)
        decision = evaluate(
            {"correlation_id": message.message_id, "home_id": self.home_id,
             "device_id": target[0], "action": wire.get("action"), "params": wire.get("params", {})},
            context, self.policies, now=now,
        )
        if decision.allowed:
            for rule_id in decision.policy_ids:
                self.counts[rule_id].append(now)
        rules = f" [{', '.join(decision.policy_ids)}]" if decision.policy_ids else ""
        return PolicyDecision("approved" if decision.allowed else "rejected",
                              f"guard:{decision.code}", decision.reason + rules,
                              RiskLevel(decision.risk or "critical"))
