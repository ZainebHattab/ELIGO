# ELIGO ai/ package (Data & AI pole)

Python functions called by the Django app. Development calls them and never re-implements their logic.

## Contract (agreed at G1, do not change without telling the other pole)

```python
from ai import evaluate_match, answer_question, generate_letter, generate_cv

evaluate_match(profile: dict, program: dict) -> {"status", "score", "reasons", "missing"}
answer_question(question: str, program_id: int | None) -> {"answer", "citations", "found"}
generate_letter(profile: dict, program: dict) -> {"text"}
generate_cv(profile: dict, program: dict) -> {"sections"}
```

### evaluate_match output
| key | type | notes |
| --- | --- | --- |
| status | str | `eligible`, `partially_eligible` or `not_eligible` |
| score | int | 0 to 100 |
| reasons | list | `{"source": "scheme"|"program", "text": str}` (+ optional `criterion_id`), plain language for a student |
| missing | list | `{"source": "scheme"|"program", "field": str, "text": str}`: profile data to add, never a crash |

Status rule (dictionary v0.6): a failed `hard` criterion gives `not_eligible`; a failed `as_a_rule` criterion gives
`partially_eligible`; `soft` only moves the score. Status needs both scheme and program criteria to pass.
The cycle label (open, closed, upcoming) is computed by the app from the program dates and is not part of this result.

## Current state: STUBS (gate G2)
All four functions return fixed samples in the exact shape, so the matches page can be built now.
`evaluate_match` ignores its inputs. For UI testing, add `"_stub_status": "eligible"` (or `"not_eligible"`) to the
program dict to see the other badges. `ai.matching.IS_STUB` is `True` until the engine replaces it at G3.

## Layout
```
ai/
  __init__.py        the four functions
  types.py           output shapes and constants (statuses, sources)
  config.py          settings from environment variables (.env.example)
  matching/          stub.py now; operators.py, engine.py, templates.py, loader.py at G3
  rag.py             answer_question stub (Sprint 3); index_source placeholder (G5)
  generation.py      generate_letter, generate_cv stubs (Sprint 4)
  tests/             contract tests, must still pass with the real engine
notebooks/           CRISP-DM pages and exploration
```

## Use in a Django view
```python
from ai import evaluate_match
result = evaluate_match(profile_dict, program_dict)   # profile_dict built from the Profile models
```

## Run
```
pip install -r requirements.txt
pytest ai/tests
```
