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
- `app/simulation`: supported Smart Home device registry
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

Multiple allowed origins can be separated by commas.

## Tests

```powershell
pytest
```

## V1 limitations

- the verifier only checks the known device registry and boolean values
- no policy rules, permissions, rate limits, or physical device adapters
- Ollama calls are synchronous
- the Universal JSON Bus currently supports only `user_situation`

The next security step is extracting `jabfy-guard` into a more advanced policy
and verification layer before any real device executor is introduced.
