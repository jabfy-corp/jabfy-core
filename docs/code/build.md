# jabfy-core — build, Docker et CI

| fichier | ce qu'il fait |
|---|---|
| `pyproject.toml` | Python ≥ 3.11 ; dépend de fastapi, httpx, jsonschema, pydantic, uvicorn, `jabfy-bus[mqtt]`, `jabfy-guard`. |
| `Dockerfile` | `python:3.11-slim`, `CMD uvicorn app.main:app --host 0.0.0.0 --port 8000` ; guard fourni par un contexte de build supplémentaire (voir compose). |
| `config/bus.json` | Les 2 policies de Core : `core_lights_v1` (switch/light, turn_on/off/toggle/set_brightness, risque max medium) et `core_thermostat_v1` (climate, set_temperature, risque max high). Rien pour `lock` ⇒ unlock refusé. |
| `.env.example` | Variables `JABFY_*` documentées. |
| `.github/workflows/ci.yml` | `pytest` sous Python 3.11. |
| `.github/workflows/pr-validation.yml` | Vérifie que la PR est liée à une issue existante. |
| `.github/workflows/publish-image.yml` | Construit et publie l'image Docker. |
| `.github/workflows/issue-labeler.yml`, `ISSUE_TEMPLATE/`, `CODEOWNERS` | Organisation GitHub, pas de logique applicative. |
