# `app/core/guard.py`

> **Rôle** — Adaptateur entre le bus et jabfy-guard : construit les règles guard depuis `config/bus.json` + l'inventaire, puis juge chaque commande.

Dépôt : [jabfy-core](README.md) · 104 lignes · statut : **actif**

## À retenir

- `CoreGuard` l.40 ; `load` l.49 : une règle guard par policy de `bus.json`, limitée aux appareils de ses domaines.
- `allow_sensitive_simulation` seulement si la policy accepte un risque ≥ HIGH l.68.
- `__call__` l.73 : refus `UNTRUSTED_TARGET` l.77-82 si la source n'est pas `core_orchestrator`, entité inconnue, protocole ≠ zigbee, topic ≠ inventaire ou champ en trop.
- Compteur par règle sur 60 s → limite 60/min.
- `bus.json` n'autorise que lumières/interrupteurs et thermostat : `unlock` (domaine `lock`) → aucune règle → refus par défaut.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 18 | `SOURCE` | constante |
| 19 | `ROLE` | constante |
| 20 | `MAX_PER_MINUTE` | constante |
| 23 | `_parameters()` |  |
| 40 | classe `CoreGuard` | méthodes : `__init__` 41, `load` 49, `__call__` 73 |

## Relations

- **Utilise** : jabfy_bus/core/message.py (jabfy-bus), jabfy_bus/core/types.py (jabfy-bus), jabfy_bus/verification/policies.py (jabfy-bus), [app/schemas/simulation.py](schemas-simulation.md), src/jabfy_guard/__init__.py (jabfy-guard)
- **Utilisé par** : [app/core/bus_runtime.py](bus-runtime.md)
- **Testé par** : `tests/test_guard.py` → [tests de jabfy-core](tests.md)
