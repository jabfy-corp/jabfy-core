# `app/core/llm_client.py`

> **Rôle** — Contrat (`Protocol`) d'un client modèle + fabrique `build_llm_client` selon `JABFY_LLM_PROVIDER`.

Dépôt : [jabfy-core](README.md) · 36 lignes · statut : **actif**

## À retenir

- `LLMClient` l.9 : `list_models`, `propose`, `close`.
- `build_llm_client` l.24 : seul `openai_compat` existe.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 9 | classe `LLMClient` | méthodes : `list_models` 10, `propose` 12, `close` 21 |
| 24 | `build_llm_client()` |  |

## Relations

- **Utilise** : [app/core/config.py](config.md), [app/core/errors.py](errors.md), [app/core/openai_client.py](openai-client.md), [app/schemas/generation.py](schemas-generation.md)
- **Utilisé par** : [app/core/action_orchestrator.py](action-orchestrator.md), [app/main.py](main.md), [app/simulation/planner.py](simulation-planner.md)
- **Testé par** : `tests/test_llm_client.py` → [tests de jabfy-core](tests.md)
