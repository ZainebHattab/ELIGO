"""Matching engine. At G3 the import below switches from the stub to engine.py.

Planned modules (Sprint 2 plan, tasks 4 to 6):
    operators.py  one function per operator (eq, neq, in, not_in, gte, lte, between, contains,
                  not_contains, contains_any); missing profile data returns "missing", never raises
    engine.py     evaluate scheme criteria and program criteria separately, then combine:
                  hard fail -> not_eligible, as_a_rule fail -> partially_eligible, soft -> score only
    templates.py  plain-language reason templates for students
    loader.py     reads the criteria export (CSV or fixtures) and expands template rows such as D-M07
"""
from .stub import IS_STUB, evaluate_match, sample_result

__all__ = ["evaluate_match", "sample_result", "IS_STUB"]
