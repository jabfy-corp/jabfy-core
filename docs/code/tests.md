# jabfy-core — tests

Total : **67 tests** répartis dans 12 fichiers (comptés par `def test_`).

| fichier | tests | code importé |
|---|---|---|
| `tests/integration/test_pipeline.py` | 1 | — |
| `tests/test_action_parser.py` | 3 | [app/core/action_parser.py](action-parser.md) |
| `tests/test_generation_params.py` | 5 | [app/schemas/generation.py](schemas-generation.md) |
| `tests/test_guard.py` | 4 | jabfy_bus/config.py (jabfy-bus), jabfy_bus/core/message.py (jabfy-bus), jabfy_bus/core/types.py (jabfy-bus), [app/core/bus_runtime.py](bus-runtime.md), [app/core/config.py](config.md), [app/core/guard.py](guard.md), [app/schemas/simulation.py](schemas-simulation.md) |
| `tests/test_headless.py` | 13 | jabfy_bus/config.py (jabfy-bus), jabfy_bus/core/message.py (jabfy-bus), jabfy_bus/core/types.py (jabfy-bus), [app/core/action_orchestrator.py](action-orchestrator.md), [app/core/bus_runtime.py](bus-runtime.md), [app/core/config.py](config.md), [app/core/run_journal.py](run-journal.md), [app/main.py](main.md), [app/schemas/simulation.py](schemas-simulation.md) |
| `tests/test_llm_client.py` | 6 | [app/core/config.py](config.md), [app/core/llm_client.py](llm-client.md), [app/core/openai_client.py](openai-client.md) |
| `tests/test_openai_client.py` | 11 | [app/core/errors.py](errors.md), [app/core/openai_client.py](openai-client.md), [app/schemas/generation.py](schemas-generation.md) |
| `tests/test_prompt_builder.py` | 3 | [app/core/prompt_builder.py](prompt-builder.md) |
| `tests/test_sanitize.py` | 7 | [app/core/sanitize.py](sanitize.md), [app/schemas/simulation.py](schemas-simulation.md), [app/simulation/planner.py](simulation-planner.md) |
| `tests/test_simulation.py` | 10 | [app/core/config.py](config.md), [app/core/errors.py](errors.md), [app/main.py](main.md), [app/schemas/simulation.py](schemas-simulation.md), [app/simulation/client.py](simulation-client.md) |
| `tests/test_simulation_readiness.py` | 1 | [app/simulation/client.py](simulation-client.md) |
| `tests/test_verification.py` | 3 | [app/core/verification.py](verification.md) |

## À retenir

- `test_headless.py` est le plus important : séquence dans l'ordre et à l'heure, refus du bus qui arrête la séquence, capteur + cooldown.
- `test_action_parser`, `test_prompt_builder`, `test_verification` testent du code hérité non monté.
- Lancer : `pytest` à la racine du dépôt, une fois l'[installation](../installation.md) faite.
