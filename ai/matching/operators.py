"""Operators of the rule engine: one small function per operator.

Each function answers one question: does the student's value (`actual`)
satisfy the value written in the criterion (`expected`)? It returns True or False.

Operators never receive None. "Unknown" is handled one level up (step 4c),
because the engine must report it as *missing*, not as a failure.
A badly written criterion (wrong type, bad range) raises ValueError: that is a
bug in our data, not a student's problem, so it must be loud.
"""
from __future__ import annotations

import re
from collections.abc import Callable, Collection, Mapping, Sequence
from datetime import date, datetime
from typing import Any

# Ranked scales from the data dictionary v0.6. Only the ordering operators
# (gte, lte, between) use ranks. eq / in compare the raw values, because
# `master` and `engineering_cycle` have the same rank but are not equal.
SCALES: dict[str, dict[str, int]] = {
    "degree_level": {
        "none": -1, "secondary": 0, "bachelor": 1,
        "engineering_cycle": 2, "master": 2, "phd": 3,
    },
    "cefr": {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6, "native": 7},
}

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

Operator = Callable[[Any, Any], bool]


# ---------- helpers ----------

def to_date(value: Any) -> date | None:
    """A date, a datetime or an ISO string 'YYYY-MM-DD' becomes a date; anything else gives None."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and _ISO_DATE.match(value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _rank_pair(actual: Any, expected: Any) -> tuple[int, int] | None:
    """Ranks of both values if they belong to the same scale, else None."""
    if not (isinstance(actual, str) and isinstance(expected, str)):
        return None
    for scale in SCALES.values():
        if actual in scale and expected in scale:
            return scale[actual], scale[expected]
    return None


def _comparable(actual: Any, expected: Any) -> tuple[Any, Any]:
    """Put two values in a form Python can order: ranks, dates or numbers."""
    ranks = _rank_pair(actual, expected)
    if ranks is not None:
        return ranks
    actual_date, expected_date = to_date(actual), to_date(expected)
    if actual_date is not None and expected_date is not None:
        return actual_date, expected_date
    if isinstance(actual, str) or isinstance(expected, str):
        raise ValueError(f"Cannot order {actual!r} and {expected!r}: not a number, a date or the same scale.")
    return actual, expected


def _as_collection(value: Any, role: str) -> Collection[Any]:
    """Lists, tuples and sets only. A str would turn `in` into a substring test ('TN' in 'TNX')."""
    if isinstance(value, (str, bytes)) or not isinstance(value, Collection):
        raise ValueError(f"{role} must be a list, got {value!r}.")
    return value


# ---------- equality ----------

def eq(actual: Any, expected: Any) -> bool:
    return actual == expected


def neq(actual: Any, expected: Any) -> bool:
    return actual != expected


# ---------- membership of a value in a criterion list ----------

def in_(actual: Any, expected: Any) -> bool:
    return actual in _as_collection(expected, "Criterion value")


def not_in(actual: Any, expected: Any) -> bool:
    return not in_(actual, expected)


# ---------- ordering (numbers, dates, ranked scales) ----------

def gte(actual: Any, expected: Any) -> bool:
    left, right = _comparable(actual, expected)
    return bool(left >= right)


def lte(actual: Any, expected: Any) -> bool:
    left, right = _comparable(actual, expected)
    return bool(left <= right)


def between(actual: Any, expected: Any) -> bool:
    """Inclusive: both bounds are allowed values."""
    if isinstance(expected, str) or not isinstance(expected, Sequence) or len(expected) != 2:
        raise ValueError(f"between needs [min, max], got {expected!r}.")
    low, high = expected
    return gte(actual, low) and lte(actual, high)


# ---------- list fields (nationalities, previous_awards, ...) ----------

def contains(actual: Any, expected: Any) -> bool:
    return expected in _as_collection(actual, "Profile value")


def not_contains(actual: Any, expected: Any) -> bool:
    return not contains(actual, expected)


def contains_any(actual: Any, expected: Any) -> bool:
    """The profile list shares at least one value with the criterion list."""
    profile_list = _as_collection(actual, "Profile value")
    return any(item in profile_list for item in _as_collection(expected, "Criterion value"))


OPERATORS: Mapping[str, Operator] = {
    "eq": eq, "neq": neq, "in": in_, "not_in": not_in,
    "gte": gte, "lte": lte, "between": between,
    "contains": contains, "not_contains": not_contains, "contains_any": contains_any,
}


def apply_operator(name: str, actual: Any, expected: Any) -> bool:
    try:
        operator = OPERATORS[name]
    except KeyError:
        raise ValueError(f"Unknown operator {name!r}.") from None
    return operator(actual, expected)
