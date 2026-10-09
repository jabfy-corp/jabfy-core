# jabfy-core

Local-first orchestration engine for JABFY. This repository extracts the useful
backend behavior from `jabfy-prototype` into a reusable API for desktop, web,
and mobile clients.

## V1 scope

- Smart Home / IoT only
- llama.cpp as the model backend, reached through its OpenAI-compatible API,
  with sampling parameters exposed
- normalized JSON action proposals
- deterministic validation before changes are returned as executable
- no real device execution and no secrets stored in the repository

Email, calendar, messaging, enterprise integrations, voice, and TTS are
deliberately outside this version.

## Architecture

```text
Client -> FastAPI -> Universal JSON Bus normalization
       -> model proposal -> JSON parser -> Verification Engine
       -> validated response
```

The main modules are:

- `app/api`: HTTP routes
- `app/core`: model backends, prompts, parsing, verification, and orchestration
- `app/schemas`: API and Universal JSON Bus contracts
- `app/simulation`: legacy device registry and live simulator discovery/proposals
- `tests`: focused unit tests for deterministic behavior

## Installation

Python 3.11 or newer and one reachable model backend are required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
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

Request an action proposal:

```bash
curl -X POST http://localhost:8000/act \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-model",
    "prompt": "User enters the house",
    "device_state": {
      "hallway_light": false,
      "garage_door": true
    },
    "params": {
      "temperature": 0.2,
      "top_k": 20,
      "n_predict": 300
    }
  }'
```

### Generation parameters

`params` is optional, and so is every field inside it. An omitted field is not
sent to the server, which then applies its own default.

| Field | Type | Range |
| --- | --- | --- |
| `temperature` | float | `0.0` - `2.0` |
| `top_p` | float | `0.0` - `1.0` |
| `top_k` | int | `>= 0` |
| `min_p` | float | `0.0` - `1.0` |
| `max_tokens` (alias `n_predict`) | int | `>= 1` |
| `seed` | int | any |
| `stop` | list of strings | any |

Unknown fields are rejected with HTTP 422 rather than silently ignored.

Names are those of the OpenAI API, forwarded to llama.cpp as-is.

Example response:

```json
{
  "action_chain": "User arrived home: turning on hallway light",
  "changes": {
    "hallway_light": true
  },
  "verification": {
    "allowed": true,
    "reason": "All requested device changes are valid.",
    "safe_changes": {
      "hallway_light": true
    }
  }
}
```

Only `safe_changes` are copied to top-level `changes`. Unknown devices,
non-boolean values, and malformed model output are rejected.

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
It uses the same `LLMClient` and `JABFY_LLM_*` configuration as `/act`. The
OpenAI-compatible backend receives the proposal JSON Schema in `response_format`
and a temperature of zero. It must support JSON-schema structured responses;
the deterministic capability checks still run after generation. `/act` retains
its optional generation parameters and does not receive a response schema.
The model receives the actual home and custom device IDs; `/act` retains its
existing static-registry contract. Names and inventory text are explicitly
treated as untrusted data in the model prompt. The entire proposal is checked
against device capabilities and parameter JSON Schemas, including nested color
values, required fields, numeric limits, and strict integer types. An invalid
command rejects the whole proposal. Local schema references are supported;
external schema references are rejected.

These endpoints never execute or publish device commands. The simulation UI
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

## Universal JSON Bus

`POST /act` is normalized internally to this first bus contract:

```json
{
  "source": "smart_home_simulation",
  "event_type": "user_situation",
  "payload": {
    "prompt": "User enters the house",
    "device_state": {
      "hallway_light": false
    }
  }
}
```

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

## V1 limitations

- `/act` verification checks the legacy device registry and boolean values;
  `/simulation/propose` checks the current simulator's advertised capabilities
- no policy rules, permissions, rate limits, or physical device adapters
- backend calls are synchronous and not streamed
- the Universal JSON Bus currently supports only `user_situation`
- reasoning models that return their output in `reasoning_content` leave
  `content` empty, and the proposal is then rejected by the parser
- `min_p` is ignored by backends that do not implement it

In the V0.0.1 virtual-home stack, final authorization is performed by jabfy-guard
inside the simulator's Bus pipeline, after the user applies a proposal. Core remains
proposal-only and rejects inventory from an inactive simulation. Set
`JABFY_LLM_BASE_URL=http://ollama:11434/v1` and
`JABFY_SIMULATION_URL=http://jabfy-sim:8080` in the shared Docker network.
See the sibling jabfy-deploy repository's `docs/v0.0.1.md` for the complete launcher.
Physical device execution and authenticated multi-user operation remain out of scope.
