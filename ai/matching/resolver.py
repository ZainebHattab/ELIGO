"""Field resolver: reads one criterion field for one student and one program.

The result is the value, or None when the value is UNKNOWN (absent, null or empty
text). The engine (step 4c) turns None into "missing". False, 0 and [] are known values.

A field can be:
  - a profile field                    "current_level"
  - a computed field                   "age_at_deadline", "gpa_percent", ...
  - a language path                    "language:en"                                  (CEFR level, bare path)
                                       "language:en.certificate_score"
                                       "language:en.certificate_age_years_at_deadline"
Fields starting with "program." are checked when the catalogue is loaded, never here.

Computed fields read program["deadline"] and program["start_date"]. If that date is
null, the computed field is unknown, so the criteria that depend on it return missing.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date
from decimal import Decimal, DivisionByZero, InvalidOperation
from typing import Any

from ai.matching.operators import SCALES, to_date

Record = Mapping[str, Any]
Resolver = Callable[[Record, Record], Any]

DAYS_PER_YEAR = 365.25


# ---------- small helpers ----------

def _get(record: Record, key: str) -> Any:
    """Value of a key, with None and empty text both meaning unknown."""
    value = record.get(key)
    return None if value is None or value == "" else value


def _date(record: Record, key: str) -> date | None:
    return to_date(record.get(key))


def _rank(level: str) -> int:
    try:
        return SCALES["degree_level"][level]
    except KeyError:
        raise ValueError(f"Unknown degree level {level!r}.") from None


def _years_between(start: date | None, end: date | None) -> float | None:
    """Decimal years from start to end (negative if end is before start). None if a date is unknown."""
    if start is None or end is None:
        return None
    return (end - start).days / DAYS_PER_YEAR


def _full_years(birth: date, on: date) -> int:
    return on.year - birth.year - ((on.month, on.day) < (birth.month, birth.day))


# Three-valued logic: True, False or None (unknown).
# `False and unknown` is False; `True or unknown` is True; otherwise unknown stays unknown.
def _and(*values: bool | None) -> bool | None:
    if any(v is False for v in values):
        return False
    return None if any(v is None for v in values) else True


def _or(*values: bool | None) -> bool | None:
    if any(v is True for v in values):
        return True
    return None if any(v is None for v in values) else False


def _test(value: Any, predicate: Callable[[Any], bool]) -> bool | None:
    return None if value is None else bool(predicate(value))


# ---------- computed fields ----------

def age_at_deadline(profile: Record, program: Record) -> int | None:
    birth, deadline = _date(profile, "date_of_birth"), _date(program, "deadline")
    return None if birth is None or deadline is None else _full_years(birth, deadline)


def _years_since_degree(profile: Record, program: Record, date_field: str) -> float | None:
    obtained = _date(profile, date_field)
    if obtained is not None:
        return _years_between(obtained, _date(program, "deadline"))
    if _get(profile, "highest_degree") == "secondary":
        return 0.0          # no university degree yet
    return None             # a degree is held but its date is unknown


def years_since_first_degree_at_deadline(profile: Record, program: Record) -> float | None:
    return _years_since_degree(profile, program, "first_degree_date")


def years_since_highest_degree_at_deadline(profile: Record, program: Record) -> float | None:
    return _years_since_degree(profile, program, "highest_degree_date")


def _years_since_phd_start(profile: Record, program: Record, program_date: str) -> float | None:
    started = _date(profile, "phd_start_date")
    if started is not None:
        return _years_between(started, _date(program, program_date))
    level = _get(profile, "current_level")
    if level is None or level == "phd":
        return None         # a PhD may be running but its start is unknown (or we do not know the level)
    return 0.0              # no PhD started


def years_since_phd_start_at_deadline(profile: Record, program: Record) -> float | None:
    return _years_since_phd_start(profile, program, "deadline")


def years_since_phd_start_at_start(profile: Record, program: Record) -> float | None:
    return _years_since_phd_start(profile, program, "start_date")


def currently_studying_in_france(profile: Record, program: Record) -> bool | None:
    level, country = _get(profile, "current_level"), _get(profile, "institution_country")
    return _and(_test(level, lambda v: v != "none"), _test(country, lambda v: v == "FR"))


def is_enrolled_or_recent_graduate(profile: Record, program: Record) -> bool | None:
    enrolled = _test(_get(profile, "current_level"), lambda v: v != "none")
    recent = _test(years_since_highest_degree_at_deadline(profile, program), lambda y: y <= 1)
    return _or(enrolled, recent)


def meets_iaeste_level(profile: Record, program: Record) -> bool | None:
    field = _test(_get(profile, "field_of_study"), lambda v: v in ("engineering_technology", "architecture_design"))
    field_science = _test(
        _get(profile, "field_of_study"),
        lambda v: v in ("engineering_technology", "mathematics_statistics", "natural_sciences"),
    )
    years = _test(_get(profile, "post_bac_years_completed"), lambda v: v >= 3)
    advanced = _test(_get(profile, "current_level"), lambda v: v in ("master", "phd"))
    return _or(_and(field, years), _and(advanced, field_science))


def highest_degree_at_start(profile: Record, program: Record) -> str | None:
    """A student who graduates before the program starts counts as already holding that degree."""
    highest, current = _get(profile, "highest_degree"), _get(profile, "current_level")
    if highest is None or current is None:
        return None
    if _rank(current) <= _rank(highest):
        return highest
    graduation, start = _date(profile, "expected_graduation"), _date(program, "start_date")
    if graduation is None or start is None:
        return None
    return current if graduation <= start else highest


def gpa_percent(profile: Record, program: Record) -> Decimal | None:
    value, scale = _get(profile, "gpa_value"), _get(profile, "gpa_scale")
    if value is None or scale is None:
        return None
    try:   # str() first: Decimal(15.2) would carry float noise. The scale may be "20" or 20 (change 26).
        return Decimal(str(value)) / Decimal(str(scale)) * 100
    except (InvalidOperation, DivisionByZero):
        return None


COMPUTED: Mapping[str, Resolver] = {
    "age_at_deadline": age_at_deadline,
    "years_since_first_degree_at_deadline": years_since_first_degree_at_deadline,
    "years_since_highest_degree_at_deadline": years_since_highest_degree_at_deadline,
    "years_since_phd_start_at_deadline": years_since_phd_start_at_deadline,
    "years_since_phd_start_at_start": years_since_phd_start_at_start,
    "currently_studying_in_france": currently_studying_in_france,
    "is_enrolled_or_recent_graduate": is_enrolled_or_recent_graduate,
    "meets_iaeste_level": meets_iaeste_level,
    "highest_degree_at_start": highest_degree_at_start,
    "gpa_percent": gpa_percent,
}


# ---------- language paths ----------

def _resolve_language(field: str, profile: Record, program: Record) -> Any:
    code, _, attribute = field.removeprefix("language:").partition(".")
    skills = profile.get("languages") or []
    skill = next((s for s in skills if s.get("language") == code), None)
    if skill is None:
        return None         # the student did not list this language
    if attribute == "":
        return _get(skill, "cefr_level")
    if attribute == "certificate_score":
        return _get(skill, "certificate_score")
    if attribute == "certificate_age_years_at_deadline":
        return _years_between(_date(skill, "certificate_date"), _date(program, "deadline"))
    raise ValueError(f"Unknown language attribute in {field!r}.")


# ---------- entry point ----------

def resolve_field(field: str, profile: Record, program: Record) -> Any:
    """Value of `field` for this student and program; None = unknown."""
    if field.startswith("program."):
        raise ValueError(f"{field!r} is checked when the catalogue is loaded, not by the engine.")
    if field.startswith("language:"):
        return _resolve_language(field, profile, program)
    if field in COMPUTED:
        return COMPUTED[field](profile, program)
    return _get(profile, field)
