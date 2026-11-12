"""Combine criteria into a status for one student and one program (step 4d).

1. SELECT the criteria that apply to this program.
2. EVALUATE them one by one (criterion.py).
3. Give a status to each side separately: scheme criteria, then program criteria.
4. COMBINE: the final status is the weaker of the two sides ("status needs both").

Status of one side:  any BLOCKS -> not_eligible
                     else any DOWNGRADES -> partially_eligible
                     else eligible          (an EMPTY list of criteria is eligible)
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ai.matching.criterion import CriterionResult, Impact, evaluate_criterion

ALL_PROGRAMS = "all programs of scheme+track"
VARIANT_PREFIX = "variant:"


class Status(StrEnum):
    ELIGIBLE = "eligible"
    PARTIALLY_ELIGIBLE = "partially_eligible"
    NOT_ELIGIBLE = "not_eligible"


_ORDER = {Status.NOT_ELIGIBLE: 0, Status.PARTIALLY_ELIGIBLE: 1, Status.ELIGIBLE: 2}


@dataclass(frozen=True)
class Evaluation:
    status: Status
    scheme_status: Status
    program_status: Status
    results: tuple[CriterionResult, ...]   # scheme results first, then program results


# ---------- 1. select ----------

def applies_to_program(criterion: Mapping[str, Any], program: Mapping[str, Any]) -> bool:
    """Does this criterion belong to this program?

    - the scheme and the track must match;
    - program_slug (criteria written for one program) must equal the program's slug;
    - applies_to: "all programs of scheme+track", or "variant:<name>" (the program must have the
      same `variant`), or a comma-separated list of program slugs. Anything else is NOT selected.
    """
    if criterion.get("scheme_slug") != program.get("scheme_slug") or criterion.get("track") != program.get("track"):
        return False
    slug = str(program.get("slug", "")).lower()
    if criterion.get("program_slug"):
        return str(criterion["program_slug"]).lower() == slug
    applies_to = str(criterion.get("applies_to") or ALL_PROGRAMS).strip()
    if applies_to == ALL_PROGRAMS:
        return True
    if applies_to.startswith(VARIANT_PREFIX):
        return applies_to[len(VARIANT_PREFIX):] == program.get("variant")
    return slug in {token.strip().lower() for token in applies_to.split(",")}


def select_criteria(criteria: Iterable[Mapping[str, Any]], program: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [c for c in criteria if applies_to_program(c, program)]


# ---------- 3. status of one side, 4. combine ----------

def side_status(results: Sequence[CriterionResult]) -> Status:
    if any(r.impact is Impact.BLOCKS for r in results):
        return Status.NOT_ELIGIBLE
    if any(r.impact is Impact.DOWNGRADES for r in results):
        return Status.PARTIALLY_ELIGIBLE
    return Status.ELIGIBLE


def combine_statuses(scheme: Status, program: Status) -> Status:
    return min(scheme, program, key=_ORDER.__getitem__)


# ---------- 2 + all together ----------

def evaluate_criteria(
    criteria: Iterable[Mapping[str, Any]], profile: Mapping[str, Any], program: Mapping[str, Any]
) -> Evaluation:
    """Evaluate criteria that are ALREADY the right ones for this program (no selection)."""
    results = [evaluate_criterion(c, profile, program) for c in criteria]
    scheme_results = [r for r in results if r.source == "scheme"]
    program_results = [r for r in results if r.source == "program"]
    scheme, program_side = side_status(scheme_results), side_status(program_results)
    return Evaluation(
        status=combine_statuses(scheme, program_side),
        scheme_status=scheme,
        program_status=program_side,
        results=tuple(scheme_results + program_results),
    )


def evaluate_program(
    criteria: Iterable[Mapping[str, Any]], profile: Mapping[str, Any], program: Mapping[str, Any]
) -> Evaluation:
    """Select the criteria of this program from a full list, then evaluate them."""
    return evaluate_criteria(select_criteria(criteria, program), profile, program)
