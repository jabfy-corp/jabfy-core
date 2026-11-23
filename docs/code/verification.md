# `app/core/verification.py`

> **Rôle** — Ancienne vérification `verify_changes` avant guard.

Dépôt : [jabfy-core](README.md) · 31 lignes · statut : **hérité — importé seulement par `routes_actions.py` (non monté) et des tests**

## À retenir

- Remplacée par VerificationEngine + jabfy-guard.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 8 | `verify_changes()` |  |

## Relations

- **Utilise** : [app/schemas/actions.py](schemas-actions.md), [app/simulation/smart_home_devices.py](simulation-smart-home-devices.md)
- **Utilisé par** : aucun import direct (point d'entrée, appelé par HTTP, CLI ou navigateur)
- **Testé par** : `tests/test_verification.py` → [tests de jabfy-core](tests.md)
