from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.matching.match import evaluate_match
from programs.models import FundingScheme, Program
from programs.services import build_program_dict, cycle_message
from profiles.services import profile_to_dict

STATUS_RANK = {"eligible": 0, "partially_eligible": 1, "not_eligible": 2}


@dataclass(frozen=True)
class ProgramMatch:
    program: Program
    result: dict[str, Any]
    cycle_status: str
    cycle_message: str
    show_cycle_notice: bool


def _match(profile_data: dict[str, Any], program: Program) -> ProgramMatch:
    result = evaluate_match(profile_data, build_program_dict(program))
    cycle = program.cycle_status()
    # Dictionary v0.5, change 38: the expiry message only matters to students who could apply.
    notice = result["status"] in ("eligible", "partially_eligible") and cycle != "open"
    return ProgramMatch(program, result, cycle, cycle_message(program), notice)


def compute_matches(profile) -> list[ProgramMatch]:
    """Recomputed on every visit: no stored results, so they can never be stale."""
    profile_data = profile_to_dict(profile)
    programs = Program.objects.select_related("scheme").order_by("scheme__name", "name")
    return [_match(profile_data, p) for p in programs]


def group_by_scheme(matches: list[ProgramMatch]) -> list[tuple[FundingScheme, list[ProgramMatch]]]:
    """Schemes in name order; inside a scheme, best status first, then highest score."""
    groups: dict[int, tuple[FundingScheme, list[ProgramMatch]]] = {}
    for m in matches:
        groups.setdefault(m.program.scheme_id, (m.program.scheme, []))[1].append(m)
    ordered = sorted(groups.values(), key=lambda g: g[0].name)
    for _, items in ordered:
        items.sort(key=lambda m: (STATUS_RANK[m.result["status"]], -m.result["score"]))
    return ordered