# `app/core/sanitize.py`

> **Rôle** — Nettoie tout texte externe avant le modèle : caractères de contrôle/invisibles, délimiteurs de prompt, longueur.

Dépôt : [jabfy-core](README.md) · 44 lignes · statut : **actif**

Docstring du module : *Sanitisation of external strings before they reach the model (MASTER_PLAN §2.5).*

## À retenir

- `sanitize_text` l.18, `sanitize_tree` l.36 ; bornes `MAX_FIELD_LENGTH` l.7, `MAX_MESSAGE_LENGTH` l.8.
- Utilisé sur le prompt utilisateur dans `planner.py` et sur les textes dans l'orchestrateur.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 7 | `MAX_FIELD_LENGTH` | constante |
| 8 | `MAX_MESSAGE_LENGTH` | constante |
| 11 | `_DELIMITERS` | constante |
| 15 | `_WHITESPACE_CONTROLS` | constante |
| 18 | `sanitize_text()` | Drop control and invisible characters, strip prompt delimiters, bound the length. |
| 36 | `sanitize_tree()` |  |

## Relations

- **Utilise** : aucun fichier JABFY documenté (bibliothèques externes seulement)
- **Utilisé par** : [app/core/action_orchestrator.py](action-orchestrator.md), [app/simulation/planner.py](simulation-planner.md)
- **Testé par** : `tests/test_sanitize.py` → [tests de jabfy-core](tests.md)
