# `app/core/action_parser.py`

> **Rôle** — Ancien parseur : extrait des actions d'un texte libre du modèle.

Dépôt : [jabfy-core](README.md) · 40 lignes · statut : **hérité — importé seulement par `routes_actions.py` (non monté) et des tests**

## À retenir

- Remplacé par la sortie JSON contrainte (`response_format`).

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 8 | classe `ActionParseError` |  |
| 12 | `_strip_code_fence()` |  |
| 18 | `parse_action_proposal()` |  |

## Relations

- **Utilise** : [app/schemas/actions.py](schemas-actions.md)
- **Utilisé par** : aucun import direct (point d'entrée, appelé par HTTP, CLI ou navigateur)
- **Testé par** : `tests/test_action_parser.py` → [tests de jabfy-core](tests.md)
