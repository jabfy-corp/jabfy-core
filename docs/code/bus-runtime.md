# `app/core/bus_runtime.py`

> **Rôle** — Héberge le pipeline jabfy-bus **dans le process** de Core et le relie à Mosquitto via paho-mqtt.

Dépôt : [jabfy-core](README.md) · 111 lignes · statut : **actif**

## À retenir

- Constructeur l.28-53 : `UniversalJsonBus`, `AuditLog()` **en mémoire** l.36-37, `EntityRegistry`, adapter Zigbee2MQTT `core_z2m_adapter`, `CoreGuard`, `VerificationEngine(authorizer=guard)`, `ExecutionLayer(audit)` l.45.
- Transports `zigbee` et `mqtt` → `_mqtt_transport` l.47-48.
- `start` l.55 : connexion broker ; callbacks paho renvoyés sur la boucle asyncio (pas de concurrence).
- `register_inventory` l.80 recharge le guard ; `_on_connect` l.88 s'abonne à `zigbee2mqtt/#`.
- `_mqtt_transport` l.105 : `publish(qos=1)` l.109 ; « exécuté » = message mis en file localement (rc OK), pas un accusé du device.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 27 | classe `BusRuntime` | méthodes : `__init__` 28, `start` 55, `stop` 70, `connected` 77, `register_inventory` 80, `_on_connect` 88, `_on_message` 95, `_handle_mqtt` 99, `_mqtt_transport` 105 |

## Relations

- **Utilise** : jabfy_bus/adapters/zigbee2mqtt/adapter.py (jabfy-bus), jabfy_bus/audit/log.py (jabfy-bus), jabfy_bus/core/bus.py (jabfy-bus), jabfy_bus/core/registry.py (jabfy-bus), jabfy_bus/execution/executor.py (jabfy-bus), jabfy_bus/verification/engine.py (jabfy-bus), jabfy_bus/verification/policies.py (jabfy-bus), [app/core/guard.py](guard.md), [app/schemas/simulation.py](schemas-simulation.md)
- **Utilisé par** : [app/core/action_orchestrator.py](action-orchestrator.md), [app/main.py](main.md)
- **Testé par** : `tests/test_guard.py`, `tests/test_headless.py` → [tests de jabfy-core](tests.md)
