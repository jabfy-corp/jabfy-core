from collections.abc import Mapping
from typing import Any

from app.schemas.actions import VerificationDecision
from app.simulation.smart_home_devices import SUPPORTED_DEVICE_IDS


def verify_changes(changes: Mapping[str, Any]) -> VerificationDecision:
    unknown_devices = sorted(set(changes) - set(SUPPORTED_DEVICE_IDS))
    if unknown_devices:
        return VerificationDecision(
            allowed=False,
            reason=f"Unknown device(s): {', '.join(unknown_devices)}.",
            safe_changes={},
        )

    invalid_values = sorted(
        device_id for device_id, value in changes.items() if type(value) is not bool
    )
    if invalid_values:
        return VerificationDecision(
            allowed=False,
            reason=f"Non-boolean value for device(s): {', '.join(invalid_values)}.",
            safe_changes={},
        )

    return VerificationDecision(
        allowed=True,
        reason="All requested device changes are valid.",
        safe_changes=dict(changes),
    )
