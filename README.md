# jabfy-core

Local-first orchestration engine for JABFY. This repository extracts the useful
backend behavior from `jabfy-prototype` into a reusable API for desktop, web,
and mobile clients.

## V1 scope

- Smart Home / IoT only
- llama.cpp as the model backend, reached through its OpenAI-compatible API,
  with sampling parameters exposed
- normalized JSON action proposals
- the `jabfy-bus` pipeline hosted in process: every command goes through the
  bus verification engine before it is sent to an MQTT device
- no secrets stored in the repository

Email, calendar, messaging, enterprise integrations, voice, and TTS are
deliberately outside this version.

## Architecture

```text
POST /prompt or sensor transition -> user_situation on the Universal JSON Bus
  -> ActionOrchestrator -> model proposal -> command.requested
  -> jabfy-bus VerificationEngine -> ExecutionLayer -> MQTT device
```

See [docs/bus-integration.md](docs/bus-integration.md) for the full design,
run statuses, API and configuration.

The main modules are:

- `app/api`: HTTP routes
- `app/core`: model backends, bus runtime, action orchestration, run journal,
  and sanitisation
- `app/schemas`: API and Universal JSON Bus contracts
- `app/simulation`: legacy device registry and live simulator discovery/proposals
- `tests`: focused unit tests for deterministic behavior

## Installation

Python 3.11 or newer, one reachable model backend and a sibling `jabfy-bus`
checkout (not published on a package index) are required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e "../jabfy-bus[mqtt]" -e ".[dev]"
Copy-Item .env.example .env
```

### Model backend

The core talks to a llama.cpp server through its OpenAI-compatible API:
`GET {base_url}/models` and `POST {base_url}/chat/completions`.

```bash
llama-server -m /path/to/model.gguf --host 0.0.0.0 --port 8080
# JABFY_LLM_BASE_URL=http://localhost:8080/v1
```

Any other server speaking the same API works too, and a hosted provider only
needs a different base URL and a key:

```bash
# JABFY_LLM_BASE_URL=https://api.example.com/v1
# JABFY_LLM_API_KEY=sk-...
```

The key is sent as `Authorization: Bearer`, and no header is sent when it is
empty, which is what a local llama.cpp server expects.

## Run locally

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The OpenAPI documentation is available at `http://localhost:8000/docs`.

## API examples

Health:

```bash
curl http://localhost:8000/health
```

Models available on the configured backend:

```bash
curl http://localhost:8000/models
```

When the backend is unavailable, `/models` returns an empty list with
`available: false` and a diagnostic reason.

Submit a request; Core plans and executes it through the bus:

```bash
curl -X POST http://localhost:8000/prompt \
  -H "Content-Type: application/json" \
  -d '{"model": "local-model", "prompt": "Turn on the living room lamp"}'
# {"prompt_id": "..."}

curl http://localhost:8000/prompts/<prompt_id>
```

Bus state, audit chain and live events:

```bash
curl http://localhost:8000/state
curl http://localhost:8000/audit/verify
# WebSockets: /bus/events, /verification/decisions, /audit/live
```

### Custom simulated homes

`jabfy-sim ui` exposes the current home's rooms, devices, states, and action
capabilities at `/api/ai/context`. Configure `JABFY_SIMULATION_URL` with the
simulator's base URL (default `http://127.0.0.1:8080`). Discovery works without
a model backend:

```bash
curl http://localhost:8000/simulation/home
```

Propose actions using that home's current inventory:

```bash
curl -X POST http://localhost:8000/simulation/propose \
  -H "Content-Type: application/json" \
  -d '{"model":"local-model","prompt":"Éclaire le bureau à moitié."}'
```

For a home containing a dimmable light named `desk_strip_42`, a valid response
can be:

```json
{
  "explanation": "Éclairer le bureau à mi-luminosité.",
  "commands": [
    {"device_id": "desk_strip_42", "action": "set_brightness", "params": {"brightness": 127}}
  ],
  "context_revision": "the-current-home-revision"
}
```

Each proposal fetches a fresh inventory with a five-second network timeout.
It uses the `JABFY_LLM_*` configuration. The
OpenAI-compatible backend receives the proposal JSON Schema in `response_format`
and a temperature of zero. It must support JSON-schema structured responses;
the deterministic capability checks still run after generation.
The model receives the actual home and custom device IDs. Names and inventory
text are sanitised and explicitly treated as untrusted data in the model prompt. The entire proposal is checked
against device capabilities and parameter JSON Schemas, including nested color
values, required fields, numeric limits, and strict integer types. An invalid
command rejects the whole proposal. Local schema references are supported;
external schema references are rejected.

`/simulation/home` and `/simulation/propose` never execute or publish device
commands; `/prompt` does, through the bus. The simulation UI
offers valid proposals for application through the simulator's verified command
API, using `context_revision` to detect a changed home. A capability-valid proposal
can still be denied by that execution policy. An unavailable or invalid simulator
returns HTTP 503; an unavailable model backend or invalid proposal returns HTTP 502.
Setting `JABFY_SIMULATION_URL` to an empty value disables discovery with HTTP 503.
Clients cannot override the simulator destination in a request.

When running the simulator UI on port 8080, use a different port for llama.cpp:

```bash
llama-server -m /path/to/model.gguf --host 127.0.0.1 --port 8081
# Core configuration:
# JABFY_LLM_BASE_URL=http://localhost:8081/v1
# JABFY_SIMULATION_URL=http://127.0.0.1:8080
```

The existing simulator Docker stack can continue using its local Ollama server
through that server's compatible `/v1` API. No Ollama Python SDK is needed.

## Configuration

Copy `.env.example` to `.env` and adjust:

| Variable | Default |
| --- | --- |
| `JABFY_HOST` | `0.0.0.0` |
| `JABFY_PORT` | `8000` |
| `JABFY_LLM_PROVIDER` | `openai_compat` |
| `JABFY_LLM_BASE_URL` | `http://localhost:8080/v1` |
| `JABFY_LLM_API_KEY` | empty |
| `JABFY_LLM_TIMEOUT_SECONDS` | `120` |
| `JABFY_ALLOWED_ORIGINS` | `http://localhost:5173` |
| `JABFY_SIMULATION_URL` | `http://127.0.0.1:8080` |
| `JABFY_MQTT_BROKER` | empty (no MQTT) |
| `JABFY_BUS_CONFIG` | `config/bus.json` |
| `JABFY_HEADLESS_MODEL` | empty (sensors do not trigger the model) |
| `JABFY_HEADLESS_COOLDOWN_SECONDS` | `30` |

Multiple allowed origins can be separated by commas.
When Core runs in a container, use a simulator address reachable from that
container, such as `http://host.docker.internal:8080` on Docker Desktop.
For compatibility with the published simulator Compose, when `JABFY_LLM_BASE_URL`
is absent, a non-empty legacy `OLLAMA_HOST` is converted to `<host>/v1`.
An explicit `JABFY_LLM_BASE_URL` always takes precedence. New deployments should
use `JABFY_LLM_BASE_URL` directly (e.g. `http://ollama:11434/v1` inside that stack).

## Tests

```powershell
pytest
```

Full pipeline integration test (MASTER_PLAN §2.7): it starts Mosquitto in
Docker, the sibling `jabfy-simulation` checkout and Core, with a fixed
OpenAI-compatible model answer, then triggers a simulated motion and checks
`command.requested` → `command.approved` → `command.executed` on
`/bus/events`, the simulated lamp and `/audit/verify`:

```bash
JABFY_INTEGRATION=1 pytest tests/integration
```

## Conteneur et déploiement

Le dépôt publie une image OCI dans GitHub Container Registry à chaque push vers
`main` :

```text
ghcr.io/jabfy-corp/jabfy-core:latest
ghcr.io/jabfy-corp/jabfy-core:sha-<commit>
```

Pour un déploiement reproductible, utiliser le digest affiché dans le résumé du
workflow plutôt que `latest` :

```bash
docker run --rm -p 8000:8000 \
  -e JABFY_LLM_BASE_URL=http://host.docker.internal:8081/v1 \
  -e JABFY_SIMULATION_URL=http://host.docker.internal:8080 \
  ghcr.io/jabfy-corp/jabfy-core@sha256:<digest>
```

Le serveur de modèle reste un service externe : l'image ne contient ni modèle ni secret.

`jabfy-bus` n'étant pas publié, la construction locale de l'image demande son
dépôt voisin comme contexte supplémentaire :

```bash
docker build --build-context jabfy-bus=../jabfy-bus -t jabfy-core .
```

## V1 limitations

- `/simulation/propose` checks the current simulator's advertised capabilities
- verification policies (`config/bus.json`) only allow lights, switches and
  the thermostat
- runs are processed one at a time; the run journal is in memory
- reasoning models that return their output in `reasoning_content` leave
  `content` empty, and the proposal is then rejected by the parser
- `min_p` is ignored by backends that do not implement it
- actions are sent on the `zigbee` transport only (`ActionOrchestrator`), so Core
  reaches MQTT devices; simulator devices served over HTTP or Modbus are driven
  from the simulator dashboard, not from Core

In the V0.0.1 virtual-home stack, final authorization is performed by jabfy-guard
inside the simulator's Bus pipeline, after the user applies a proposal. Core remains
proposal-only and rejects inventory from an inactive simulation. Set
`JABFY_LLM_BASE_URL=http://ollama:11434/v1` and
`JABFY_SIMULATION_URL=http://jabfy-sim:8080` in the shared Docker network.
See the sibling jabfy-deploy repository's `docs/v0.0.1.md` for the complete launcher.
Physical device execution and authenticated multi-user operation remain out of scope.
