# `app/core/errors.py`

> **Rôle** — Une seule exception : `LLMClientError`, toute panne pour joindre ou lire le backend modèle.

Dépôt : [jabfy-core](README.md) · 2 lignes · statut : **actif**

## À retenir

- Levée par `openai_client.py`, traduite en HTTP 502 par `routes_simulation.py`.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 1 | classe `LLMClientError` | Any failure reaching or parsing a response from the LLM backend. |

## Relations

- **Utilise** : aucun fichier JABFY documenté (bibliothèques externes seulement)
- **Utilisé par** : [app/api/routes_actions.py](routes-actions.md), [app/api/routes_models.py](routes-models.md), [app/api/routes_simulation.py](routes-simulation.md), [app/core/action_orchestrator.py](action-orchestrator.md), [app/core/llm_client.py](llm-client.md), [app/core/openai_client.py](openai-client.md)
- **Testé par** : `tests/test_openai_client.py`, `tests/test_simulation.py` → [tests de jabfy-core](tests.md)
