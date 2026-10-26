# `app/core/config.py`

> **Rôle** — Réglages de Core lus dans les variables d'environnement `JABFY_*` (pydantic-settings).

Dépôt : [jabfy-core](README.md) · 51 lignes · statut : **actif**

## À retenir

- `Settings` l.12 : host `0.0.0.0`, port 8000, `simulation_url` `http://localhost:8080`, `llm_base_url` `http://localhost:8080/v1`, `headless_cooldown` 30 s.
- Deux défauts sur le port 8080 (simulateur et LLM) : conflit si on lance tout en local sans variables.
- `get_settings` l.28 : compatibilité `OLLAMA_HOST` l.31-35 → reprise comme `llm_base_url`.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 9 | `DEFAULT_BUS_CONFIG` | constante |
| 12 | classe `Settings` |  |
| 28 | `get_settings()` |  |

## Relations

- **Utilise** : aucun fichier JABFY documenté (bibliothèques externes seulement)
- **Utilisé par** : [app/core/llm_client.py](llm-client.md), [app/main.py](main.md)
- **Testé par** : `tests/test_guard.py`, `tests/test_headless.py`, `tests/test_llm_client.py`, `tests/test_simulation.py` → [tests de jabfy-core](tests.md)
