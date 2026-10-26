# `app/schemas/actions.py`

> **Rôle** — Modèles de l'ancienne API d'actions (PR #10).

Dépôt : [jabfy-core](README.md) · 42 lignes · statut : **hérité — importé seulement par `routes_actions.py` (non monté) et des tests**

## À retenir

- Utilisé par `routes_actions`, `action_parser`.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 8 | classe `ActionRequest` |  |
| 17 | classe `UserSituationPayload` |  |
| 22 | classe `UniversalBusEvent` |  |
| 28 | classe `ActionProposal` |  |
| 33 | classe `VerificationDecision` |  |
| 39 | classe `ActionResponse` |  |

## Relations

- **Utilise** : [app/schemas/generation.py](schemas-generation.md)
- **Utilisé par** : [app/api/routes_actions.py](routes-actions.md), [app/core/action_parser.py](action-parser.md), [app/core/verification.py](verification.md)
