# Installation et lancement

## Prérequis

- Python 3.11 ou plus récent
- Un serveur LLM joignable qui parle l'API OpenAI (llama.cpp recommandé)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
cp .env.example .env             # Windows : Copy-Item .env.example .env
```

## Serveur de modèle

jabfy-core appelle `GET {base_url}/models` et `POST {base_url}/chat/completions`. Avec llama.cpp :

```bash
llama-server -m /chemin/vers/modele.gguf --host 0.0.0.0 --port 8080
# JABFY_LLM_BASE_URL=http://localhost:8080/v1
```

Tout autre serveur compatible fonctionne, y compris un fournisseur hébergé (il suffit de changer l'URL et d'ajouter une clé). Ce choix sort du mode 100 % local.

```bash
# JABFY_LLM_BASE_URL=https://api.example.com/v1
# JABFY_LLM_API_KEY=sk-...
```

La clé est envoyée en `Authorization: Bearer`. Si elle est vide, aucun en-tête n'est envoyé, ce qu'attend un llama.cpp local.

## Lancement

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

La documentation OpenAPI générée est sur `http://localhost:8000/docs`. Vérification rapide :

```bash
curl http://localhost:8000/health
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
| `JABFY_ALLOWED_ORIGINS` | `http://localhost:5173` | Origines CORS autorisées, séparées par des virgules |

Ne commitez jamais `.env` ni de clé d'API.
