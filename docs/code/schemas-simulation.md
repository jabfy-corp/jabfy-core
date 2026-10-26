# `app/schemas/simulation.py`

> **Rôle** — Modèles pydantic partagés : inventaire du simulateur, commande proposée, proposition du modèle.

Dépôt : [jabfy-core](README.md) · 117 lignes · statut : **actif**

Docstring du module : *Dynamic simulation inventory and proposal-only API contracts.*

## À retenir

- `MAX_SEQUENCE_MS = 60_000` l.91 ; `SimulationCommand.delay_ms` 0–10 000 l.100 ; somme des délais ≤ 60 s vérifiée l.111.
- `ModelProposal` l.103 : le schéma JSON envoyé au LLM.
- Contient le bloc `bus` d'un appareil (`entity_id`, `domain`, `topic`).

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 8 | classe `InventoryModel` |  |
| 12 | classe `SimulationRoom` |  |
| 17 | classe `SimulationHome` |  |
| 23 | classe `SimulationCapability` |  |
| 29 | classe `SimulationBusBinding` |  |
| 35 | classe `SimulationDevice` |  |
| 47 | classe `SimulationContext` | méthodes : `supported_version` 57, `simulation_only` 64, `unambiguous_inventory` 70 |
| 84 | classe `ProposalRequest` |  |
| 91 | `MAX_SEQUENCE_MS` | constante |
| 94 | classe `SimulationCommand` |  |
| 103 | classe `ModelProposal` | méthodes : `bounded_sequence` 110 |
| 116 | classe `SimulationProposal` |  |

## Relations

- **Utilise** : aucun fichier JABFY documenté (bibliothèques externes seulement)
- **Utilisé par** : [app/api/routes_bus.py](routes-bus.md), [app/api/routes_simulation.py](routes-simulation.md), [app/core/action_orchestrator.py](action-orchestrator.md), [app/core/bus_runtime.py](bus-runtime.md), [app/core/guard.py](guard.md), [app/simulation/client.py](simulation-client.md), [app/simulation/planner.py](simulation-planner.md)
- **Testé par** : `tests/test_guard.py`, `tests/test_headless.py`, `tests/test_sanitize.py`, `tests/test_simulation.py` → [tests de jabfy-core](tests.md)
