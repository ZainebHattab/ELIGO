"""evaluate_match(): the public function of the matching engine (step 4e).

OUTPUT CONTRACT (frozen, unchanged):
    {"status": "eligible" | "partially_eligible" | "not_eligible",
     "score": int 0-100,
     "reasons": [{"source": "scheme" | "program", "text": str}],
     "missing": [{"source": "scheme" | "program", "field": str, "text": str}]}

INPUT: `profile` is the student's dict. `program` is the program record (dictionary v0.6) PLUS one
optional key, `program["criteria"]`: the list of criteria that apply to this program (scheme level and
program level), each with id, scope, field, operator, value, strength, to_verify. The Django view builds
that list from the EligibilityCriterion rows; the ai/ package never touches the database.
Without that key, there is nothing to check and the result is `eligible`.

The target level is checked like any other criterion: the program's degree_level_offered must equal the
student's target_degree_level (hard, source program). A different target gives not_eligible,
an unknown target gives partially_eligible.

The wording of reasons and missing items below is a PLACEHOLDER: task 6 replaces describe_* with templates.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypedDict

from ai.matching.criterion import CriterionResult, Impact, Outcome
from ai.matching.engine import evaluate_criteria
from ai.matching.scoring import compute_score


class Reason(TypedDict):
    source: str
    text: str


class MissingItem(TypedDict):
    source: str
    field: str
    text: str


class MatchResult(TypedDict):
    status: str
    score: int
    reasons: list[Reason]
    missing: list[MissingItem]


TARGET_LEVEL_ID = "TARGET-LEVEL"
_SEVERITY = {Impact.BLOCKS: 0, Impact.DOWNGRADES: 1, Impact.NONE: 2}   # most serious first


# ---------- placeholder wording (task 6 replaces these two functions) ----------

def describe_failure(result: CriterionResult) -> str:
    return f"Requirement not met: {result.field} {result.operator} {result.expected} (your value: {result.actual})."


def describe_missing(result: CriterionResult) -> str:
    return f"We need your {result.field} to check this requirement."


# ---------- building the result ----------

def _target_level_criterion(program: Mapping[str, Any]) -> dict[str, Any] | None:
    offered = program.get("degree_level_offered")
    if not offered:
        return None         # a program record without this field cannot be checked
    return {"id": TARGET_LEVEL_ID, "scope": "program", "field": "target_degree_level",
            "operator": "eq", "value": offered, "strength": "hard"}


def _reasons(results: list[CriterionResult]) -> list[Reason]:
    failed = sorted((r for r in results if r.outcome is Outcome.FAIL), key=lambda r: _SEVERITY[r.impact])
    return [{"source": r.source, "text": describe_failure(r)} for r in failed]


def _missing(results: list[CriterionResult]) -> list[MissingItem]:
    # A missing soft criterion changes nothing, so the student is not asked for it.
    missing = [r for r in results if r.outcome is Outcome.MISSING and r.impact is not Impact.NONE]
    return [{"source": r.source, "field": r.field, "text": describe_missing(r)} for r in missing]


def evaluate_match(profile: Mapping[str, Any], program: Mapping[str, Any]) -> MatchResult:
    criteria: list[Mapping[str, Any]] = list(program.get("criteria") or [])
    target = _target_level_criterion(program)
    if target is not None:
        criteria.append(target)

    evaluation = evaluate_criteria(criteria, profile, program)
    results = list(evaluation.results)
    return {
        "status": evaluation.status.value,
        "score": compute_score(evaluation.status, results),
        "reasons": _reasons(results),
        "missing": _missing(results),
    }
