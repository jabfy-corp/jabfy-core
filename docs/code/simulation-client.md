# `app/simulation/client.py`

> **Rôle** — Client HTTP vers le simulateur : lit l'inventaire de la maison (`GET /api/ai/context`).

Dépôt : [jabfy-core](README.md) · 53 lignes · statut : **actif**

Docstring du module : *Read a configured simulator catalog; never accept an upstream URL from a request.*

## À retenir

- `fetch_context` l.28, requête l.42 ; échec → `SimulationUnavailable`.
- Le contenu (domaine, `entity_id`, `topic`) est cru sans recoupement : le simulateur est une source de confiance.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 12 | classe `SimulationUnavailable` |  |
| 16 | classe `SimulationClient` | méthodes : `__init__` 17, `fetch_context` 28 |

## Relations

- **Utilise** : [app/schemas/simulation.py](schemas-simulation.md)
- **Utilisé par** : [app/api/routes_simulation.py](routes-simulation.md), [app/core/action_orchestrator.py](action-orchestrator.md), [app/main.py](main.md), [app/simulation/planner.py](simulation-planner.md)
- **Testé par** : `tests/test_simulation.py`, `tests/test_simulation_readiness.py`, `tests/test_stack_integration.py` → [tests de jabfy-core](tests.md)
