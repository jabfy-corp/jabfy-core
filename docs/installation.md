# Installation et lancement

## Prérequis

- Python 3.11 ou plus récent
- Un serveur LLM joignable qui parle l'API OpenAI (llama.cpp recommandé), avec réponses structurées par JSON Schema
- Les dépôts voisins `jabfy-bus` et `jabfy-guard`, qui ne sont pas publiés sur un index de paquets
- Pour piloter des appareils : jabfy-simulation et un broker MQTT (Mosquitto)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .\.venv\Scripts\Activate.ps1
python -m pip install -e "../jabfy-bus[mqtt]" -e "../jabfy-guard" -e ".[dev]"
cp .env.example .env             # Windows : Copy-Item .env.example .env
```

## Serveur de modèle

jabfy-core appelle `GET {base_url}/models` et `POST {base_url}/chat/completions`. Avec llama.cpp, sur un port différent de celui du simulateur (8080) :

```bash
llama-server -m /chemin/vers/modele.gguf --host 127.0.0.1 --port 8081
# JABFY_LLM_BASE_URL=http://localhost:8081/v1
```

Tout autre serveur compatible fonctionne, y compris un fournisseur hébergé (il suffit de changer l'URL et d'ajouter une clé). Ce choix sort du mode 100 % local.

La clé est envoyée en `Authorization: Bearer`. Si elle est vide, aucun en-tête n'est envoyé, ce qu'attend un llama.cpp local.

## Lancement

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

La documentation OpenAPI générée est sur `http://localhost:8000/docs`. Vérification rapide :

```bash
curl http://localhost:8000/health
curl http://localhost:8000/simulation/home
```

## Configuration

Variables d'environnement (fichier `.env`) :

| Variable | Défaut | Rôle |
|---|---|---|
| `JABFY_HOST` | `0.0.0.0` | Adresse d'écoute |
| `JABFY_PORT` | `8000` | Port d'écoute |
| `JABFY_LLM_PROVIDER` | `openai_compat` | Type de backend (seul `openai_compat` existe) |
| `JABFY_LLM_BASE_URL` | `http://localhost:8080/v1` | URL de l'API du modèle |
| `JABFY_LLM_API_KEY` | vide | Clé d'API, facultative |
| `JABFY_LLM_TIMEOUT_SECONDS` | `120` | Délai maximal d'un appel au modèle |
| `JABFY_ALLOWED_ORIGINS` | `http://localhost:5173` | Origines CORS et WebSocket autorisées, séparées par des virgules |
| `JABFY_SIMULATION_URL` | `http://127.0.0.1:8080` | URL de jabfy-simulation ; vide = découverte désactivée (503) |
| `JABFY_MQTT_BROKER` | vide | `hôte:port` du broker MQTT ; vide = pas de MQTT, les commandes échouent |
| `JABFY_BUS_CONFIG` | `config/bus.json` | Fichier des politiques de vérification |
| `JABFY_HEADLESS_MODEL` | vide | Modèle utilisé pour les exécutions déclenchées par capteur ; vide = désactivé |
| `JABFY_HEADLESS_COOLDOWN_SECONDS` | `30` | Délai minimal entre deux exécutions d'un même capteur |

Si `JABFY_LLM_BASE_URL` est absent, une variable `OLLAMA_HOST` non vide est convertie en `<hôte>/v1`, pour rester compatible avec le Compose du simulateur. Une valeur explicite de `JABFY_LLM_BASE_URL` est toujours prioritaire.

Dans un conteneur, utiliser une adresse de simulateur joignable depuis ce conteneur, par exemple `http://host.docker.internal:8080` sous Docker Desktop.

Ne commitez jamais `.env` ni de clé d'API.

## Image Docker

La construction locale de l'image demande les dépôts voisins comme contextes supplémentaires :

```bash
docker build --build-context jabfy-bus=../jabfy-bus --build-context jabfy-guard=../jabfy-guard -t jabfy-core .
```

L'image ne contient ni modèle ni secret : le serveur de modèle reste un service externe.
