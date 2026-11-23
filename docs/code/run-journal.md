# `app/core/run_journal.py`

> **Rôle** — Journal des runs : garde pour chaque run son statut et ses étapes (requested → approved/rejected → executed/failed) en écoutant le bus.

Dépôt : [jabfy-core](README.md) · 94 lignes · statut : **actif**

Docstring du module : *Bounded per-run record built from bus messages.*

## À retenir

- `TERMINAL` l.15 et `STEP_RANK` l.17.
- `STEP_RANK` existe parce que le bus dispatche en profondeur d'abord : la décision et le résultat arrivent **avant** que `command.requested` soit noté ; le rang monotone l.85 empêche de revenir en arrière.
- `_on_command` l.72 relie les messages au run par `correlation_id`.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 15 | `TERMINAL` | constante |
| 17 | `STEP_RANK` | constante |
| 20 | `_now()` |  |
| 24 | classe `RunJournal` | méthodes : `__init__` 25, `attach` 30, `create` 34, `get` 47, `status` 51, `update` 55, `add_step` 63, `_on_command` 72, `_on_event` 91 |

## Relations

- **Utilise** : jabfy_bus/core/bus.py (jabfy-bus), jabfy_bus/core/message.py (jabfy-bus)
- **Utilisé par** : [app/core/action_orchestrator.py](action-orchestrator.md), [app/main.py](main.md)
- **Testé par** : `tests/test_headless.py` → [tests de jabfy-core](tests.md)
