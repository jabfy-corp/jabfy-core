# `app/main.py`

> **Rôle** — Point d'entrée FastAPI : construit l'application, branche le bus en process, le journal des runs, l'orchestrateur et les routes.

Dépôt : [jabfy-core](README.md) · 87 lignes · statut : **actif**

## À retenir

- `create_app` l.25 assemble tout ; `lifespan` l.28-43 démarre/arrête le bus MQTT et le worker de l'orchestrateur.
- CORS l.51-57 depuis `settings.allowed_origins`.
- Objets partagés sur `app.state` : `BusRuntime` l.63, `RunJournal` l.64-65, `ActionOrchestrator` l.66-74.
- Routers montés l.79-82 : health, models, simulation, bus ; puis WebSocket `/bus/events` l.83. `routes_actions` n'est **pas** monté.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 25 | `create_app()` |  |

## Relations

- **Utilise** : jabfy_bus/api/ws.py (jabfy-bus), jabfy_bus/config.py (jabfy-bus), [app/api/routes_bus.py](routes-bus.md), [app/api/routes_health.py](routes-health.md), [app/api/routes_models.py](routes-models.md), [app/api/routes_simulation.py](routes-simulation.md), [app/core/action_orchestrator.py](action-orchestrator.md), [app/core/bus_runtime.py](bus-runtime.md), [app/core/config.py](config.md), [app/core/llm_client.py](llm-client.md), [app/core/run_journal.py](run-journal.md), [app/simulation/client.py](simulation-client.md)
- **Utilisé par** : aucun import direct (point d'entrée, appelé par HTTP, CLI ou navigateur)
- **Testé par** : `tests/test_headless.py`, `tests/test_simulation.py`, `tests/test_stack_integration.py` → [tests de jabfy-core](tests.md)

## Questions fréquentes

- « Où démarre Core ? » → `create_app`, puis `lifespan`.
- « Pourquoi `routes_actions` existe encore ? » → code hérité de PR #10, non monté.
