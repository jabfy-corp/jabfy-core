# `app/simulation/planner.py`

> **Rôle** — Transforme une demande en plan : construit le prompt système avec l'inventaire, appelle le LLM, valide la réponse.

Dépôt : [jabfy-core](README.md) · 135 lignes · statut : **actif**

Docstring du module : *Build proposals from a live inventory and validate every command before returning it.*

## À retenir

- `propose` l.67 ; prompt système l.78-111 (inventaire en JSON).
- Appel `temperature=0` + schéma `ModelProposal` l.112-117.
- Validation l.118-132 : JSON strict (NaN refusé), appareil connu, action supportée, paramètres validés ; sinon `InvalidSimulationProposal`.
- Le plan = explication + liste de commandes avec délais ; il est validé ici puis **re-jugé** par guard à chaque commande.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 18 | classe `InvalidSimulationProposal` |  |
| 31 | `_reject_constant()` |  |
| 35 | `_reject_external_references()` | Capability schemas are self-contained; validation must never fetch remote resources. |
| 51 | `_validators()` |  |
| 67 | `propose()` |  |

## Relations

- **Utilise** : [app/core/llm_client.py](llm-client.md), [app/core/sanitize.py](sanitize.md), [app/schemas/generation.py](schemas-generation.md), [app/schemas/simulation.py](schemas-simulation.md), [app/simulation/client.py](simulation-client.md)
- **Utilisé par** : [app/api/routes_simulation.py](routes-simulation.md), [app/core/action_orchestrator.py](action-orchestrator.md)
- **Testé par** : `tests/test_sanitize.py` → [tests de jabfy-core](tests.md)
