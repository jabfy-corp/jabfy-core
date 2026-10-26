# `app/core/prompt_builder.py`

> **Rôle** — Ancien constructeur de prompt (PR #10).

Dépôt : [jabfy-core](README.md) · 34 lignes · statut : **hérité — importé seulement par `routes_actions.py` (non monté) et des tests**

## À retenir

- Remplacé par le prompt de `planner.py`.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 5 | `SYSTEM_PROMPT` | constante |
| 23 | `build_state_context()` |  |
| 33 | `build_user_message()` |  |

## Relations

- **Utilise** : [app/simulation/smart_home_devices.py](simulation-smart-home-devices.md)
- **Utilisé par** : aucun import direct (point d'entrée, appelé par HTTP, CLI ou navigateur)
- **Testé par** : `tests/test_prompt_builder.py` → [tests de jabfy-core](tests.md)
