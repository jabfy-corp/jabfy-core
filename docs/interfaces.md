# Interfaces

La spécification complète des routes HTTP est générée par FastAPI : `http://localhost:8000/docs` (Swagger) et `/openapi.json`.

## API HTTP

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/health` | `{"status": "ok", "service": "jabfy-core"}` |
| GET | `/models` | Modèles disponibles sur le backend |
| POST | `/prompt` | Lance une exécution : plan du modèle puis commandes vérifiées |
| GET | `/prompts/{prompt_id}` | État d'une exécution et de ses étapes |
| GET | `/state` | Connexion MQTT et entités connues |
| GET | `/audit/verify` | Vérifie la chaîne de hachage du journal d'audit |
| GET | `/simulation/home` | Inventaire de la maison simulée |
| POST | `/simulation/propose` | Proposition d'actions, sans exécution |

### `GET /models`

```json
{ "models": ["local-model"], "available": true, "reason": null }
```

Si le backend est injoignable : `models: []`, `available: false` et un `reason`.

### `POST /prompt`

```bash
curl -X POST http://localhost:8000/prompt \
  -H "Content-Type: application/json" \
  -d '{"model": "local-model", "prompt": "Allume la lampe du salon"}'
```

```json
{"prompt_id": "3f0c…"}
```

| Champ | Type | Obligatoire |
|---|---|---|
| `model` | string | oui |
| `prompt` | string | oui |

| Code | Cas |
|---|---|
| 202 | Exécution acceptée, traitée en arrière-plan |
| 422 | Corps invalide |
| 429 | Trop d'exécutions en attente |

### `GET /prompts/{prompt_id}`

```json
{
  "id": "3f0c…",
  "source": "prompt",
  "model": "local-model",
  "request": "Allume la lampe du salon",
  "status": "completed",
  "explanation": "Allumer la lampe du salon.",
  "error": null,
  "steps": [
    {
      "device_id": "salon_lamp", "action": "turn_on", "params": {}, "delay_ms": 0,
      "request_id": "9a1e…", "status": "executed", "reason": null,
      "history": [
        {"status": "requested", "time": "…"},
        {"status": "approved", "time": "…"},
        {"status": "executed", "time": "…"}
      ]
    }
  ],
  "created_at": "…",
  "finished_at": "…"
}
```

HTTP 404 pour une exécution inconnue ou sortie du journal. Les statuts sont décrits dans [Fonctionnement interne](fonctionnement.md#statuts).

### `GET /state`

```json
{
  "mqtt_connected": true,
  "entities": [
    {"id": "…", "domain": "light", "class": "…", "location": "…", "last_value": "…", "last_seen": "…"}
  ]
}
```

### `GET /audit/verify`

```json
{"verified": true, "records": 42}
```

### `GET /simulation/home` et `POST /simulation/propose`

`/simulation/home` renvoie l'inventaire courant du simulateur (pièces, appareils, états, capacités). `/simulation/propose` prend le même corps que `/prompt` et renvoie une proposition **sans l'exécuter** :

```json
{
  "explanation": "Éclairer le bureau à mi-luminosité.",
  "commands": [
    {"device_id": "desk_strip_42", "action": "set_brightness", "params": {"brightness": 127}, "delay_ms": 0}
  ],
  "context_revision": "…"
}
```

`context_revision` permet au simulateur de détecter une maison modifiée entre la proposition et son application.

| Code | Cas |
|---|---|
| 503 | Simulateur indisponible, inventaire invalide ou simulation inactive |
| 502 | Backend du modèle indisponible ou proposition invalide |

## WebSockets

Fournies par jabfy-bus, elles diffusent les messages du bus en direct :

| Route | Contenu |
|---|---|
| `/bus/events` | Tous les messages du bus |
| `/verification/decisions` | Décisions de vérification |
| `/audit/live` | Entrées du journal d'audit |

Une connexion de navigateur n'est acceptée que si son `Origin` figure dans `JABFY_ALLOWED_ORIGINS` ; un client sans en-tête `Origin` (CLI, tests) est accepté.

## Messages publiés sur le bus

| Type | Quand |
|---|---|
| `user_situation` | `POST /prompt`, ou transition d'un capteur en mode autonome |
| `automation.core_reasoning` | Explication du plan par le modèle |
| `command.requested` | Chaque commande du plan, sur le transport `zigbee` |

Les décisions (`command.approved`, `command.rejected`) et les résultats (`command.executed`) sont publiés par jabfy-bus. Le format des messages est celui de jabfy-bus (page `message-schema.md` de jabfy-bus).

## Appels sortants

| Cible | Appel |
|---|---|
| Serveur LLM | `GET {JABFY_LLM_BASE_URL}/models`, `POST {JABFY_LLM_BASE_URL}/chat/completions` |
| jabfy-simulation | `GET {JABFY_SIMULATION_URL}/api/ai/context`, délai réseau de 5 secondes |
| Broker MQTT | publication sur `<topic>/set` de l'appareil |
