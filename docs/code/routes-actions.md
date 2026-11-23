# `app/api/routes_actions.py`

> **Rôle** — Ancienne route d'actions : prompt → texte libre → parseur d'actions → vérification.

Dépôt : [jabfy-core](README.md) · 18 lignes · statut : **hérité — importé seulement par `routes_actions.py` (non monté) et des tests**

## À retenir

- Non incluse par `main.py` l.79-82 : inaccessible en HTTP.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 13 | `act()` |  |

## Relations

- **Utilise** : [app/core/errors.py](errors.md), [app/schemas/actions.py](schemas-actions.md)
- **Utilisé par** : aucun import direct (point d'entrée, appelé par HTTP, CLI ou navigateur)
