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
- `app/simulation`: supported Smart Home device registry
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
| `JABFY_LLM_BASE_URL` | `http://localhost:8080/v1` |
| `JABFY_LLM_API_KEY` | empty |
| `JABFY_ALLOWED_ORIGINS` | `http://localhost:5173` |

Multiple allowed origins can be separated by commas.

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

- the verifier only checks the known device registry and boolean values
- no policy rules, permissions, rate limits, or physical device adapters
- backend calls are synchronous and not streamed
- the Universal JSON Bus currently supports only `user_situation`
- reasoning models that return their output in `reasoning_content` leave
  `content` empty, and the proposal is then rejected by the parser
- `min_p` is ignored by backends that do not implement it

The next security step is extracting `jabfy-guard` into a more advanced policy
and verification layer before any real device executor is introduced.
