from __future__ import annotations

from datetime import date
from typing import Any

from django.db.models import Q

from .models import EligibilityCriterion, Program

CHECK = "Check the official page before preparing."


def _fmt(d: date) -> str:
    return f"{d.day} {d.strftime('%B %Y')}"


def cycle_message(program: Program, today: date | None = None) -> str:
    """One line shown next to the cycle status (dictionary v0.6, changes 42 and 43)."""
    today = today or date.today()
    status = program.cycle_status(today)
    estimated = program.deadline_basis == "estimated"

    if status == "upcoming":
        text = f"The call opens around {_fmt(program.opening_date)}."
        return f"{text} {CHECK}" if estimated else text

    if status == "open":
        dates = [d for d in (program.deadline, program.host_deadline) if d]
        if program.deadline_rounds:
            dates = [date.fromisoformat(d) for d in program.deadline_rounds]
            dates = [d for d in dates if d >= today]
        if not dates:
            return "Applications are open."
        nxt = min(dates)
        if estimated:
            return f"The deadline is expected around {_fmt(nxt)}, based on this year. {CHECK}"
        return f"Apply before {_fmt(nxt)}."

    if status == "closed":
        if not program.next_expected_deadline:
            return "No confirmed next call."
        if estimated:
            return f"The next call is expected around {_fmt(program.next_expected_deadline)}, based on this year. {CHECK}"
        return f"Next deadline: {_fmt(program.next_expected_deadline)}."

    return "No deadline published yet."
def criterion_to_dict(criterion: EligibilityCriterion) -> dict[str, Any]:
    """One criterion row as the plain dict the engine reads (`id` = the CSV code)."""
    return {
        "id": criterion.code,
        "scope": criterion.scope,
        "field": criterion.field,
        "operator": criterion.operator,
        "value": criterion.value,
        "strength": criterion.strength,
        "to_verify": criterion.to_verify,
        "cycle": criterion.cycle,
    }


def criteria_for_program(program: Program) -> list[EligibilityCriterion]:
    """Scheme-level rules (same scheme and track) + this program's own rules, scheme first."""
    return list(
        EligibilityCriterion.objects
        .filter(scheme=program.scheme, track=program.track)
        .filter(Q(scope="scheme", program__isnull=True) | Q(program=program))
        .order_by("-scope", "code")
    )


def build_program_dict(program: Program) -> dict[str, Any]:
    """The `program` argument of evaluate_match(): program record + program["criteria"]."""
    return {
        "id": program.pk,
        "slug": program.slug,
        "name": program.name,
        "scheme_slug": program.scheme.slug,
        "track": program.track,
        "degree_level_offered": program.degree_level_offered,
        "field_of_study": program.field_of_study,
        "language_of_instruction": program.language_of_instruction,
        "country": program.country,
        "opening_date": program.opening_date,
        "deadline": program.deadline,
        "host_deadline": program.host_deadline,
        "deadline_rounds": list(program.deadline_rounds),
        "start_date": program.start_date,
        "criteria": [criterion_to_dict(c) for c in criteria_for_program(program)],
    }