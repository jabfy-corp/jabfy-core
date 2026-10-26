# `app/core/action_orchestrator.py`

> **Rôle** — Le cerveau du mode headless : reçoit les événements du bus, demande un plan au LLM et publie les commandes une par une, à l'heure.

Dépôt : [jabfy-core](README.md) · 200 lignes · statut : **actif**

Docstring du module : *Bus participant (MASTER_PLAN §2.2): situations in, command.requested out.*

## À retenir

- `attach` l.72 s'abonne à `user_situation`, `telemetry`, `state_changed`.
- `on_event` l.92 / `_on_sensor` l.100 : un capteur de mouvement qui passe à vrai déclenche un run, puis cooldown l.108-110 (30 s par défaut).
- `_enqueue` l.121 → file asyncio bornée ; `_worker` l.127 traite **un run à la fois**.
- `_run` l.136 : `fetch_context` **une seule fois** l.139, `register_inventory` l.140, `propose` avec `wait_for` l.141-147, `no_action` l.157-159.
- Boucle l.163 : `sleep(delay)` l.164 puis `command.requested` l.173-181 (cible = `device.bus.topic`), `bus.publish` l.183 ; arrêt si `rejected`/`failed` l.184-188 ; `completed` l.189.
- Statuts du run : `queued` (l.95/118) → `planning` l.137 → `running` l.161 → `completed` / `rejected` / `failed` / `no_action`.
- Le contexte n'est jamais relu pendant la séquence (jusqu'à 60 s) ; pas d'annulation.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 29 | `ADAPTER` | constante |
| 30 | `SENSOR_DOMAIN` | constante |
| 34 | classe `Job` |  |
| 40 | classe `ActionOrchestrator` | méthodes : `__init__` 41, `bus` 69, `attach` 72, `start` 77, `stop` 81, `full` 89, `on_event` 92, `_on_sensor` 100, `_enqueue` 121, `_worker` 127, `_run` 136, `_publish_reasoning` 191 |

## Relations

- **Utilise** : jabfy_bus/core/message.py (jabfy-bus), jabfy_bus/core/types.py (jabfy-bus), [app/core/bus_runtime.py](bus-runtime.md), [app/core/errors.py](errors.md), [app/core/llm_client.py](llm-client.md), [app/core/run_journal.py](run-journal.md), [app/core/sanitize.py](sanitize.md), [app/schemas/simulation.py](schemas-simulation.md), [app/simulation/client.py](simulation-client.md), [app/simulation/planner.py](simulation-planner.md)
- **Utilisé par** : [app/main.py](main.md)
- **Testé par** : `tests/test_headless.py` → [tests de jabfy-core](tests.md)

## Questions fréquentes

- « Montre-moi où la commande part » → l.183.
- « Que se passe-t-il si la lampe est éteinte à la main pendant la séquence ? » → rien, contexte périmé.
