# Tests

jabfy-core a 30 tests unitaires (pytest). Ils ne demandent ni serveur de modèle ni réseau : le transport `httpx` est remplacé par un faux dans les tests du client.

## Lancer les tests

```bash
python -m pip install -e ".[dev]"
pytest                                          # tous les tests
pytest tests/test_verification.py               # un fichier
pytest tests/test_verification.py::test_rejects_unknown_device   # un seul test
```

La CI (`ci.yml`) lance `pytest` en Python 3.11 sur chaque PR vers `main`.

## Ce que couvre chaque fichier

| Fichier | Tests | Ce qui est vérifié |
|---|---|---|
| `test_action_parser.py` | 3 | JSON extrait d'un bloc Markdown, JSON entouré de texte, rejet d'une réponse sans JSON |
| `test_verification.py` | 3 | Rejet d'un appareil inconnu, rejet d'une valeur non booléenne, acceptation d'un changement valide |
| `test_prompt_builder.py` | 3 | Contexte d'état des appareils (avec et sans appareils), message utilisateur |
| `test_generation_params.py` | 6 | Paramètres omis non envoyés, tous les paramètres documentés, alias `n_predict`, température hors plage, paramètre inconnu rejeté, `params` vide par défaut |
| `test_llm_client.py` | 5 | Choix du client selon `JABFY_LLM_PROVIDER`, URL et délai transmis, erreur sur un fournisseur inconnu, défaut sur llama.cpp local |
| `test_openai_client.py` | 10 | Liste des modèles, transmission des paramètres d'échantillonnage, absence de `choices`, en-tête `Authorization` présent ou absent, erreurs HTTP et corps `{"error": …}` convertis en `LLMClientError`, fermeture du client |

## Ce qui n'est pas testé

- les routes HTTP (`/health`, `/models`, `/act`) et le code 502 ;
- l'orchestrateur de bout en bout (événement, modèle, parsing, vérification) ;
- un vrai serveur llama.cpp : aucun test d'intégration n'existe.

## Ajouter un test

- Un fichier par module, nommé `tests/test_<module>.py`, avec des fonctions `test_…` sans classe.
- Pour le client LLM, injecter un `httpx.MockTransport` via le paramètre `transport` plutôt que d'appeler un vrai serveur.
- Une modification du comportement du vérificateur (`app/core/verification.py`) doit s'accompagner d'un test dans `test_verification.py`.
