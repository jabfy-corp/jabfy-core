# Interfaces

La spécification complète et à jour est générée par FastAPI : `http://localhost:8000/docs` (Swagger) et `/openapi.json`.

## API HTTP

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/health` | `{"status": "ok", "service": "jabfy-core"}` |
| GET | `/models` | Modèles disponibles sur le backend |
| POST | `/act` | Proposition d'actions vérifiée |

### `GET /models`

```json
{ "models": ["local-model"], "available": true, "reason": null }
```

Si le backend est injoignable : `models: []`, `available: false` et un `reason`.

### `POST /act`

```bash
curl -X POST http://localhost:8000/act \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-model",
    "prompt": "User enters the house",
    "device_state": { "hallway_light": false, "garage_door": true },
    "params": { "temperature": 0.2, "top_k": 20, "n_predict": 300 }
  }'
```

| Champ | Type | Obligatoire |
|---|---|---|
| `model` | string | oui |
| `prompt` | string, la situation | oui |
| `device_state` | objet `id d'appareil → booléen` | non |
| `params` | paramètres de génération | non |

Réponse :

```json
{
  "action_chain": "User arrived home: turning on hallway light",
  "changes": { "hallway_light": true },
  "verification": {
    "allowed": true,
    "reason": "All requested device changes are valid.",
    "safe_changes": { "hallway_light": true }
  }
}
```

`changes` ne contient que les `safe_changes`. Si la proposition est refusée, `changes` est vide et `verification.reason` explique pourquoi.

| Code | Cas |
|---|---|
| 200 | Réponse normale, y compris une proposition refusée par le vérificateur |
| 422 | Corps invalide, champ inconnu (y compris dans `params`) |
| 502 | Backend du modèle indisponible |

### Paramètres de génération (`params`)

Tous facultatifs. Les noms sont ceux de l'API OpenAI, transmis tels quels à llama.cpp.

| Champ | Type | Plage |
|---|---|---|
| `temperature` | float | `0.0` à `2.0` |
| `top_p` | float | `0.0` à `1.0` |
| `top_k` | int | `>= 0` |
| `min_p` | float | `0.0` à `1.0` |
| `max_tokens` (alias `n_predict`) | int | `>= 1` |
| `seed` | int | quelconque |
| `stop` | liste de chaînes | quelconque |

## Appareils reconnus

`hallway_light`, `hallway_window`, `living_room_light`, `living_room_window`, `living_room_tv`, `kitchen_light`, `kitchen_window`, `bedroom_light`, `bedroom_window`, `bathroom_light`, `bathroom_window`, `garage_light`, `garage_door`, `house_lock`, `climatisation`, `heater`, `alarm`.

## Contrat de bus (mini-version)

Sur `main`, `/act` est normalisé en interne vers un premier contrat inspiré du Universal JSON Bus. Seul `user_situation` existe :

```json
{
  "source": "smart_home_simulation",
  "event_type": "user_situation",
  "payload": {
    "prompt": "User enters the house",
    "device_state": { "hallway_light": false }
  }
}
```

Ce contrat n'est pas celui de jabfy-bus (schémas v1.0 dans le dépôt jabfy-bus).

## Appels sortants

| Cible | Appel |
|---|---|
| Serveur LLM | `GET {JABFY_LLM_BASE_URL}/models`, `POST {JABFY_LLM_BASE_URL}/chat/completions` (`stream: false`) |
