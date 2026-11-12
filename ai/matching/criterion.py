"""Evaluation of ONE criterion for one student and one program (step 4c).

Two separate questions are answered here:
  1. outcome: did the student pass, fail, or is the answer MISSING (unknown value)?
  2. impact:  what does that outcome do to the status? It depends on the strength.

    strength     fail                       missing                   pass
    hard         BLOCKS (not_eligible)      DOWNGRADES (partial)      none
    as_a_rule    DOWNGRADES (partial)       DOWNGRADES (partial)      none
    soft         none (score only)          none (score only)         none

A missing criterion never fails the student and never crashes the engine.
But the student cannot be `eligible` while something that matters is still unknown.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ai.matching.operators import apply_operator
from ai.matching.resolver import resolve_field

STRENGTHS = ("hard", "as_a_rule", "soft")
SOURCES = ("scheme", "program")


class Outcome(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    MISSING = "missing"


class Impact(StrEnum):
    NONE = "none"
    DOWNGRADES = "downgrades"   # status cannot be better than partially_eligible
    BLOCKS = "blocks"           # status is not_eligible


@dataclass(frozen=True)
class CriterionResult:
    id: str
    source: str            # "scheme" or "program" (the criterion's scope)
    field: str
    strength: str
    outcome: Outcome
    impact: Impact
    actual: Any            # the student's value, None when missing
    to_verify: bool        # the criterion itself still needs checking against the official source
    operator: str = ""     # kept for the reason templates (task 6)
    expected: Any = None


def impact_of(outcome: Outcome, strength: str) -> Impact:
    if strength not in STRENGTHS:
        raise ValueError(f"Unknown strength {strength!r}.")
    if outcome is Outcome.PASS or strength == "soft":
        return Impact.NONE
    if outcome is Outcome.FAIL and strength == "hard":
        return Impact.BLOCKS
    return Impact.DOWNGRADES


def _require(criterion: Mapping[str, Any], key: str) -> Any:
    if key not in criterion:
        raise ValueError(f"Criterion {criterion.get('id', '?')} has no {key!r}.")
    return criterion[key]


def evaluate_criterion(criterion: Mapping[str, Any], profile: Mapping[str, Any], program: Mapping[str, Any]) -> CriterionResult:
    field, operator, strength = (_require(criterion, k) for k in ("field", "operator", "strength"))
    source = _require(criterion, "scope")
    if source not in SOURCES:
        raise ValueError(f"Criterion {criterion.get('id', '?')}: unknown scope {source!r}.")

    actual = resolve_field(field, profile, program)
    if actual is None:
        outcome = Outcome.MISSING
    elif apply_operator(operator, actual, _require(criterion, "value")):
        outcome = Outcome.PASS
    else:
        outcome = Outcome.FAIL

    return CriterionResult(
        id=str(criterion.get("id", "")), source=source, field=field, strength=strength,
        outcome=outcome, impact=impact_of(outcome, strength), actual=actual,
        to_verify=bool(criterion.get("to_verify", False)),
        operator=operator, expected=criterion.get("value"),
    )
