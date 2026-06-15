from collections.abc import Mapping

from app.simulation.smart_home_devices import SUPPORTED_DEVICE_IDS

SYSTEM_PROMPT = f"""You are a Smart Home automation controller.
You receive the current device states and a situation.
Return ONLY one raw JSON object, without markdown or explanation.

Required format:
{{"action_chain":"<one sentence describing the proposal>","changes":{{"<device_id>":true}}}}

Available device IDs: {", ".join(SUPPORTED_DEVICE_IDS)}

Rules:
- Only propose changes for available device IDs.
- Values in "changes" must be JSON booleans.
- Only include devices whose state needs to change.
- If nothing needs to change, return an empty "changes" object.
- You propose actions only. A deterministic verifier decides whether they are safe.
"""


def build_state_context(device_state: Mapping[str, bool]) -> str:
    if not device_state:
        return "Current device state: all devices are off."

    lines = ["Current device state:"]
    for device_id, state in device_state.items():
        lines.append(f"  {device_id}: {'ON' if state else 'OFF'}")
    return "\n".join(lines)


def build_user_message(prompt: str, device_state: Mapping[str, bool]) -> str:
    return f"{build_state_context(device_state)}\n\nSituation: {prompt}"
