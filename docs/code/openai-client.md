# `app/core/openai_client.py`

> **Rôle** — Client HTTP pour toute API compatible OpenAI (llama.cpp, Ollama `/v1`, cloud).

Dépôt : [jabfy-core](README.md) · 88 lignes · statut : **actif**

## À retenir

- `propose` l.45 envoie `/chat/completions` avec message système + utilisateur.
- `response_format` `json_schema` l.62-66 : force le modèle à répondre selon le schéma `ModelProposal`.
- llama.cpp peut répondre 200 avec `{error}` : traité comme erreur.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 9 | classe `OpenAICompatibleClient` | Client for any OpenAI-compatible chat API. — méthodes : `__init__` 22, `list_models` 36, `propose` 45, `close` 87 |

## Relations

- **Utilise** : [app/core/errors.py](errors.md), [app/schemas/generation.py](schemas-generation.md)
- **Utilisé par** : [app/core/llm_client.py](llm-client.md)
- **Testé par** : `tests/test_llm_client.py`, `tests/test_openai_client.py`, `tests/test_stack_integration.py` → [tests de jabfy-core](tests.md)
