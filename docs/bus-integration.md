# Bus integration and headless reasoning

This document describes the changes on branch `core-12-bus-integration`
(MASTER_PLAN Phase 2). It is meant both for readers new to Jabfy and for
developers reviewing the pull request.

## What changed, in one paragraph

Core no longer only *proposes* actions. It now hosts the `jabfy-bus` pipeline
in its own process (MASTER_PLAN Option A), subscribes to bus events, asks the
model for a plan, and publishes each resulting command as `command.requested`.
Every command still goes through the bus `VerificationEngine` before the
`ExecutionLayer` sends it to the device over MQTT. The model never calls a
device directly. The legacy `POST /act` endpoint is no longer mounted.

## Architecture

```text
                       ┌──────────────────────── Core process ───────────────────────┐
POST /prompt ─────────▶│ user_situation ─┐                                           │
                       │                 ▼                                           │
MQTT (Zigbee2MQTT) ───▶│ Zigbee2MQTTAdapter ─▶ UniversalJsonBus ◀─ ActionOrchestrator │
                       │                         │   ▲              (queue, 1 worker) │
                       │                         │   │ command.requested              │
                       │                         ▼   │                                │
                       │                 VerificationEngine ─▶ ExecutionLayer ──────▶│──▶ MQTT <topic>/set
                       │                         │                                   │
                       │                 AuditLog (hash chain), EntityRegistry,      │
                       │                 RunJournal (per-run steps)                  │
                       └─────────────────────────────────────────────────────────────┘
```

| Module | Role |
|---|---|
| `app/core/bus_runtime.py` | `BusRuntime`: bus, audit log, entity registry, Zigbee2MQTT adapter, verification engine and execution layer. One paho client serves both the adapter and the `zigbee`/`mqtt` transports; paho callbacks are handed back to the asyncio loop. `register_inventory()` declares the simulator devices to the registry. |
| `app/core/action_orchestrator.py` | Bus participant. Turns a situation into a model run, then publishes the commands one by one. |
| `app/core/run_journal.py` | Keeps the last 100 runs and the status of each step, read by `GET /prompts/{id}`. |
| `app/core/sanitize.py` | Cleans every external string before it reaches the model. |
| `app/api/routes_bus.py` | `/prompt`, `/prompts/{id}`, `/state`, `/audit/verify`. |
| `config/bus.json` | Verification policies used by Core. |

## Runs

A run starts in one of two ways:

1. **Prompt** — `POST /prompt` publishes a `user_situation` message on the bus.
2. **Sensor transition** — when `JABFY_HEADLESS_MODEL` is set, a change of
   value on a `binary_sensor` entity (motion, door contact, leak…) starts a run
   with a sanitised description of the transition. Each entity has a cooldown
   (`JABFY_HEADLESS_COOLDOWN_SECONDS`, default 30 s). Without the variable,
   sensors never trigger the model.

Runs go through a bounded queue (16 jobs) consumed by a single worker, so two
runs never interleave. When the queue is full, `POST /prompt` answers 429.

For each run the orchestrator:

1. fetches the current home from the simulator and registers its devices;
2. asks the model for a proposal (bounded by `JABFY_LLM_TIMEOUT_SECONDS`);
3. publishes a reasoning event (`automation.core_reasoning`) with the
   explanation;
4. publishes each command as `command.requested` on the `zigbee` transport,
   after waiting its `delay_ms`;
5. stops at the first command that is rejected or fails.

### Statuses

| Run status | Meaning |
|---|---|
| `queued` | Waiting for the worker. |
| `planning` | Inventory and model call in progress. |
| `running` | Commands being published. |
| `completed` | Every command was executed. |
| `no_action` | The model proposed no command. |
| `rejected` | The verification engine refused a command. |
| `failed` | Simulator, model, transport or internal error (see `error`). |

Step statuses: `pending`, `requested`, `approved`, `rejected`, `executed`,
`failed`.

### Timed sequences

A proposed command may carry `delay_ms` (0 to 10 000) — the wait before it is
published. A proposal holds at most 60 commands and its delays add up to at
most 60 seconds. This allows requests such as "turn the living room lamps on
one after another, two seconds apart".

## HTTP and WebSocket API

### `POST /prompt`

```bash
curl -X POST http://localhost:8000/prompt \
  -H "Content-Type: application/json" \
  -d '{"model": "local-model", "prompt": "Turn on the living room lamp"}'
```

```json
{"prompt_id": "3f0c…"}
```

HTTP 202. The run is processed in the background.

### `GET /prompts/{prompt_id}`

```json
{
  "id": "3f0c…",
  "source": "prompt",
  "model": "local-model",
  "request": "Turn on the living room lamp",
  "status": "completed",
  "explanation": "Turning on the living room lamp.",
  "error": null,
  "steps": [
    {
      "device_id": "salon_lamp", "action": "turn_on", "params": {}, "delay_ms": 0,
      "request_id": "9a1e…", "status": "executed", "reason": null,
      "history": [
        {"status": "requested", "time": "…"},
        {"status": "approved", "time": "…"},
        {"status": "executed", "time": "…"}
      ]
    }
  ],
  "created_at": "2026-10-08T10:00:00+00:00",
  "finished_at": "2026-10-08T10:00:03+00:00"
}
```

HTTP 404 for an unknown or evicted run.

### `GET /state`

MQTT connection status and the entities known to the registry (id, domain,
class, location, last value, last seen).

### `GET /audit/verify`

```json
{"verified": true, "records": 42}
```

Checks the audit log hash chain.

### WebSockets (from `jabfy-bus`)

`/bus/events`, `/verification/decisions` and `/audit/live` stream bus messages
live. A browser connection is accepted only if its `Origin` is listed in
`JABFY_ALLOWED_ORIGINS`; a client without an `Origin` header (CLI, tests) is
accepted.

## Sanitisation

Every string coming from outside (device names, rooms, states, sensor
situations) is cleaned before it is placed in the prompt:

- control, format and private-use characters are removed;
- chat-template markers (`<|…|>`, `[INST]`, `<<SYS>>`, `<system>`…) and
  Markdown fences are removed;
- line breaks become spaces in single-line fields;
- fields are limited to 200 characters, messages to 4 000.

Sanitisation reduces the attack surface; it is not the safety guarantee. The
guarantee remains the verification engine and its policies.

## Verification policies

`config/bus.json` (overridable with `JABFY_BUS_CONFIG`):

| Policy | Domains | Actions |
|---|---|---|
| `core_lights_v1` | `switch`, `light` | turn_on, turn_off, toggle, set_brightness |
| `core_thermostat_v1` | `climate` | set_temperature |

Any other command (blinds, air conditioning, locks…) is rejected by default.

## Configuration

| Variable | Default | Role |
|---|---|---|
| `JABFY_MQTT_BROKER` | empty | `host:port` of the MQTT broker. Empty: the bus runs without MQTT and commands fail. |
| `JABFY_BUS_CONFIG` | `config/bus.json` | Verification policies file. |
| `JABFY_HEADLESS_MODEL` | empty | Model used for sensor-triggered runs. Empty: disabled. |
| `JABFY_HEADLESS_COOLDOWN_SECONDS` | `30` | Minimum delay between two runs triggered by the same sensor. |

## Dependency on jabfy-bus

`pyproject.toml` depends on `jabfy-bus[mqtt]`, which is not published on a
package index. Locally:

```bash
pip install -e "../jabfy-bus[mqtt]" -e ".[dev]"
```

The image is built with an extra build context:

```bash
docker build --build-context jabfy-bus=../jabfy-bus -t jabfy-core .
```

This Core branch requires the matching jabfy-bus branch (`user_situation`
message type, `allowed_origins` on WebSocket routes).

## Tests

- `tests/test_headless.py`: orchestrator, sequences, journal, cooldown.
- `tests/test_sanitize.py`: sanitisation.
- `tests/integration/test_pipeline.py` (`JABFY_INTEGRATION=1`): Mosquitto in
  Docker, the sibling `jabfy-simulation` checkout and Core, with a fixed model
  answer. Checks `command.requested` → `command.approved` → `command.executed`,
  the simulated lamp and `/audit/verify`.

## Known limitations

- Commands are sent on the `zigbee` transport only: simulator devices served
  over HTTP or Modbus are not reachable from Core.
- Policies only cover lights, switches and the thermostat.
- The run journal is in memory (last 100 runs) and lost on restart.
- `routes_actions.py` (`/act`), `verification.py`, `action_parser.py` and
  `prompt_builder.py` are no longer used by the application.
