# jabfy-core

Local-first orchestration engine for JABFY. This repository extracts the useful
backend behavior from `jabfy-prototype` into a reusable API for desktop, web,
and mobile clients.

## V1 scope

- Smart Home / IoT only
- local Ollama model discovery and chat
- normalized JSON action proposals
- deterministic validation before changes are returned as executable
- no real device execution and no secrets stored in the repository

Email, calendar, messaging, enterprise integrations, voice, and TTS are
deliberately outside this version.

## Architecture

```text
Client -> FastAPI -> Universal JSON Bus normalization
       -> Ollama proposal -> JSON parser -> Verification Engine
       -> validated response
```

The main modules are:

- `app/api`: HTTP routes
- `app/core`: Ollama, prompts, parsing, verification, and orchestration
- `app/schemas`: API and Universal JSON Bus contracts
- `app/simulation`: legacy device registry and live simulator discovery/proposals
- `tests`: focused unit tests for deterministic behavior

## Installation

Python 3.11 or newer and a local Ollama installation are required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Start Ollama and download a model if needed:

```powershell
ollama serve
ollama pull llama3.2
```

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

Available Ollama models:

```bash
curl http://localhost:8000/models
```

When Ollama is unavailable, `/models` returns an empty list with
`available: false` and a diagnostic reason.

Request an action proposal:

```bash
curl -X POST http://localhost:8000/act \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "prompt": "User enters the house",
    "device_state": {
      "hallway_light": false,
      "garage_door": true
    }
  }'
```

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
Ollama:

```bash
curl http://localhost:8000/simulation/home
```

Propose actions using that home's current inventory:

```bash
curl -X POST http://localhost:8000/simulation/propose \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.2","prompt":"Éclaire le bureau à moitié."}'
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
returns HTTP 503; unavailable Ollama or an invalid model proposal returns HTTP 502.
Setting `JABFY_SIMULATION_URL` to an empty value disables discovery with HTTP 503.
Clients cannot override the simulator destination in a request.

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
| `OLLAMA_HOST` | `http://localhost:11434` |
| `JABFY_ALLOWED_ORIGINS` | `http://localhost:5173` |
| `JABFY_SIMULATION_URL` | `http://127.0.0.1:8080` |

Multiple allowed origins can be separated by commas.
When Core runs in a container, use a simulator address reachable from that
container, such as `http://host.docker.internal:8080` on Docker Desktop.

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
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  ghcr.io/jabfy-corp/jabfy-core@sha256:<digest>
```

Ollama reste un service externe : l'image ne contient ni modèle ni secret.

## V1 limitations

- `/act` verification checks the legacy device registry and boolean values;
  `/simulation/propose` checks the current simulator's advertised capabilities
- no policy rules, permissions, rate limits, or physical device adapters
- Ollama calls are synchronous
- the Universal JSON Bus currently supports only `user_situation`

The next security step is extracting `jabfy-guard` into a more advanced policy
and verification layer before any real device executor is introduced.
