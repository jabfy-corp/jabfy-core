# `app/api/routes_bus.py`

> **Rôle** — Routes HTTP du mode headless : soumettre une situation (`POST /prompt`), suivre un run, lire l'état et vérifier l'audit.

Dépôt : [jabfy-core](README.md) · 52 lignes · statut : **actif**

Docstring du module : *Headless entry points (MASTER_PLAN §2.4): a prompt becomes a bus situation.*

## À retenir

- `POST /prompt` l.14 : publie un `user_situation` sur le bus avec trust `INTERNAL`, renvoie 202 + `prompt_id` (= id du message, qui devient l'id du run), 429 si la file est pleine.
- `GET /prompts/{id}` l.27 lit le `RunJournal` ; `GET /state` l.35 ; `GET /audit/verify` l.49 vérifie la chaîne de hachage.
- Aucune authentification sur ces routes.

## Contenu (ligne → élément)

| ligne | élément | note |
|---|---|---|
| 15 | `prompt()` |  |
| 28 | `prompt_run()` |  |
| 36 | `state()` |  |
| 50 | `audit_verify()` |  |

## Relations

- **Utilise** : jabfy_bus/core/message.py (jabfy-bus), jabfy_bus/core/types.py (jabfy-bus), [app/schemas/simulation.py](schemas-simulation.md)
- **Utilisé par** : [app/main.py](main.md)

## Questions fréquentes

- « Qui peut appeler `/prompt` ? » → n'importe qui qui atteint le port 8000 ; dans Compose le port n'est pas publié sur l'hôte.
