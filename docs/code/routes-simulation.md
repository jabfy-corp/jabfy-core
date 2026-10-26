# `app/api/routes_simulation.py`

> **Rôle** — Mode interactif : lire la maison simulée (`GET /simulation/home`) et demander une proposition validée (`POST /simulation/propose`).

Dépôt : [jabfy-core](README.md) · 35 lignes · statut : **actif**

Docstring du module : *Read-only discovery and validated action proposals for the configured simulation.*

## À retenir

- `home` l.17 → `simulation_client.fetch_context()`, 503 si simulateur absent.
- `propose_simulation` l.25 → `planner.propose`, 502 si proposition invalide ou LLM en panne.
- Ne publie rien sur le bus : renvoie seulement la proposition.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 17 | `home()` |  |
| 25 | `propose_simulation()` |  |

## Relations

- **Utilise** : [app/core/errors.py](errors.md), [app/schemas/simulation.py](schemas-simulation.md), [app/simulation/client.py](simulation-client.md), [app/simulation/planner.py](simulation-planner.md)
- **Utilisé par** : [app/main.py](main.md)
