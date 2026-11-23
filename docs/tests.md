# Tests

jabfy-core a 96 tests unitaires et 1 test d'intégration (pytest). Les tests unitaires ne demandent ni serveur de modèle ni réseau : le transport `httpx` est remplacé par un faux dans les tests du client.

## Lancer les tests

```bash
python -m pip install -e ".[dev]"
pytest                                          # tous les tests
pytest tests/test_verification.py               # un fichier
pytest tests/test_verification.py::test_rejects_unknown_device   # un seul test
JABFY_INTEGRATION=1 pytest tests/integration    # intégration (Docker, jabfy-simulation voisin)
```

La CI (`ci.yml`) lance `pytest` en Python 3.11 sur chaque PR vers `main`.

## Ce que couvre chaque fichier

| Fichier | Tests | Ce qui est vérifié |
|---|---|---|
| `test_action_parser.py` | 3 | JSON extrait d'un bloc Markdown, JSON entouré de texte, rejet d'une réponse sans JSON |
| `test_verification.py` | 3 | Rejet d'un appareil inconnu, rejet d'une valeur non booléenne, acceptation d'un changement valide |
| `test_prompt_builder.py` | 3 | Contexte d'état des appareils (avec et sans appareils), message utilisateur |
| `test_generation_params.py` | 5 | Paramètres omis non envoyés, paramètres documentés, alias `n_predict`, valeurs hors plage et paramètres inconnus rejetés |
| `test_llm_client.py` | 7 | Choix du client selon `JABFY_LLM_PROVIDER`, URL et délai transmis, erreur sur un fournisseur inconnu, défaut sur llama.cpp local |
| `test_openai_client.py` | 11 | Liste des modèles, paramètres d'échantillonnage, absence de `choices`, en-tête `Authorization`, erreurs HTTP converties en `LLMClientError`, fermeture du client |
| `test_guard.py` | 4 | Refus tant que l'inventaire n'est pas chargé, politiques du core appliquées par jabfy-guard, seul le core commande l'inventaire, limite de débit par politique |
| `test_headless.py` | 17 | Séquences (ordre, délais, bornes), arrêt sur refus du bus, proposition invalide, déclenchement par capteur et délai de répit, file pleine refusée |
| `test_sanitize.py` | 7 | Caractères invisibles retirés, délimiteurs de gabarit neutralisés, longueur bornée, inventaire et situation nettoyés avant le modèle |
| `test_simulation.py` | 33 | Découverte de la maison, proposition sans exécution, rejet de toute la proposition sur une commande invalide, schéma des paramètres, simulateur ou modèle indisponible |
| `test_simulation_readiness.py` | 3 | Une simulation inactive n'est pas utilisée pour proposer des actions |
| `integration/test_pipeline.py` | 1 | Mosquitto, jabfy-simulation et jabfy-core : `command.requested` → `command.approved` → `command.executed` |

## Ce qui n'est pas testé

- les anciennes routes (`/act`), qui ne sont plus utilisées par l'application ;
- un vrai serveur de modèle : le test d'intégration utilise une réponse fixe.

## Ajouter un test

- Un fichier par module, nommé `tests/test_<module>.py`, avec des fonctions `test_…` sans classe.
- Pour le client LLM, injecter un `httpx.MockTransport` via le paramètre `transport` plutôt que d'appeler un vrai serveur.
- Une modification du comportement du vérificateur (`app/core/verification.py`) doit s'accompagner d'un test dans `test_verification.py`.
