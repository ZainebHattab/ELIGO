"""Turn raw criterion values into words a student knows.

Rule: nothing returned here contains an underscore, a raw slug or an operator name.
Sentences themselves live in reasons.py; this module only formats VALUES.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)

# Labels are lowercase so they read well in the middle of a sentence.
LABELS: dict[str, dict[str, str]] = {
    "degree": {
        "none": "not enrolled",
        "secondary": "secondary (baccalaureate level)",
        "bachelor": "bachelor (licence)",
        "engineering_cycle": "engineering cycle (cycle ingénieur)",
        "master": "master",
        "phd": "PhD",
    },
    "cefr": {
        "A1": "A1", "A2": "A2", "B1": "B1", "B2": "B2", "C1": "C1", "C2": "C2",
        "native": "native speaker",
    },
    "country": {
        "TN": "Tunisia", "FR": "France", "DE": "Germany", "HU": "Hungary",
        "CA": "Canada", "IT": "Italy", "GB": "the United Kingdom", "other": "another country",
    },
    "nationality": {
        "TN": "Tunisian", "FR": "French", "HU": "Hungarian", "other": "another nationality",
    },
    "field_of_study": {
        "engineering_technology": "engineering and technology",
        "mathematics_statistics": "mathematics and statistics",
        "natural_sciences": "natural sciences",
        "business_economics": "business and economics",
        "health_medicine": "health and medicine",
        "law_social_sciences": "law and social sciences",
        "humanities": "humanities",
        "arts_music_performing": "arts, music and performing arts",
        "architecture_design": "architecture and design",
        "other": "other fields",
    },
    "enrollment": {"full_time": "full time", "part_time": "part time"},
    "institution_type": {"public": "public", "private": "private"},
    "supervisor": {
        "none": "no supervisor yet",
        "contacted": "supervisor contacted",
        "confirmed": "supervisor confirmed in writing",
    },
    "award": {
        "mitacs_globalink": "Mitacs Globalink",
        "daad_study_scholarship": "DAAD study scholarship",
        "daad_doctoral": "DAAD doctoral scholarship",
        "eiffel_master": "Eiffel (master)",
        "eiffel_phd": "Eiffel (PhD)",
        "erasmus_mundus_jm": "Erasmus Mundus Joint Master",
        "chevening": "Chevening",
        "other_uk_government_scholarship": "another UK government scholarship",
        "french_government_scholarship": "a French government scholarship",
        "zuse_school_scholarship": "Zuse School scholarship",
        "stipendium_hungaricum_bachelor": "Stipendium Hungaricum (bachelor)",
        "stipendium_hungaricum_master": "Stipendium Hungaricum (master)",
        "stipendium_hungaricum_phd": "Stipendium Hungaricum (PhD)",
        "hungarian_government_scholarship": "a Hungarian government scholarship",
    },
    "hungarian_status": {
        "stateless": "stateless",
        "refugee": "refugee",
        "long_term_resident": "long-term resident",
    },
    "target_level": {
        "master": "a master's degree",
        "phd": "a PhD",
        "internship": "an internship",
    },
}

LANGUAGE_NAMES: dict[str, str] = {
    "ar": "Arabic", "fr": "French", "en": "English", "de": "German",
    "es": "Spanish", "it": "Italian", "hu": "Hungarian", "other": "another language",
}

# Which kind of value each criterion field holds.
FIELD_KIND: dict[str, str] = {
    "age_at_deadline": "years",
    "class_rank_percentile": "percent",
    "gpa_percent": "percent",
    "current_level": "degree",
    "highest_degree": "degree",
    "highest_degree_at_start": "degree",
    "date_of_birth": "date",
    "expected_graduation": "date",
    "year_of_study": "number",
    "months_resident_in_germany": "months",
    "years_since_highest_degree_at_deadline": "years",
    "years_since_phd_start_at_start": "years",
    "enrollment_mode": "enrollment",
    "institution_type": "institution_type",
    "institution_country": "country",
    "field_of_study": "field_of_study",
    "supervisor_status": "supervisor",
    "nationalities": "nationality",
    "hungarian_status_flags": "hungarian_status",
    "previous_awards": "award",
    "rejected_applications": "award",
    "target_degree_level": "target_level",
    "currently_studying_in_france": "yes_no",
    "is_enrolled_or_recent_graduate": "yes_no",
    "joint_supervision_agreement": "yes_no",
    "master_started_in_germany": "yes_no",
    "meets_iaeste_level": "yes_no",
    "pfe_agreement": "yes_no",
    "work_study_contract": "yes_no",
}

_LANGUAGE_SUFFIX_KIND = {
    "": "cefr",
    "certificate_score": "number",
    "certificate_age_years_at_deadline": "years",
}


def humanize(value: Any) -> str:
    """Safe fallback: never show underscores."""
    return str(value).replace("_", " ").strip()


def parse_language_field(field: str) -> tuple[str, str] | None:
    """'language:fr.certificate_score' -> ('fr', 'certificate_score'); None if not a language path."""
    if not field.startswith("language:"):
        return None
    code, _, suffix = field[len("language:"):].partition(".")
    return code, suffix


def language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, "another language")


def value_kind(field: str) -> str:
    parsed = parse_language_field(field)
    if parsed:
        return _LANGUAGE_SUFFIX_KIND.get(parsed[1], "number")
    return FIELD_KIND.get(field, "text")


def _to_decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def _to_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def format_number(value: Any) -> str:
    """20 -> '20', Decimal('2.50') -> '2.5', 2.3333 -> '2.33'."""
    number = _to_decimal(value)
    if number is None:
        return humanize(value)
    return f"{number.quantize(Decimal('0.01')):f}".rstrip("0").rstrip(".")


def format_percent(value: Any) -> str:
    return f"{format_number(value)}%"


def _with_unit(value: Any, singular: str) -> str:
    number = _to_decimal(value)
    unit = singular if number == 1 else f"{singular}s"
    return f"{format_number(value)} {unit}"


def format_years(value: Any) -> str:
    return _with_unit(value, "year")


def format_months(value: Any) -> str:
    return _with_unit(value, "month")


def format_date(value: Any) -> str:
    """'1997-04-01' -> '1 April 1997'."""
    parsed = _to_date(value)
    if parsed is None:
        return humanize(value)
    return f"{parsed.day} {MONTHS[parsed.month - 1]} {parsed.year}"


def format_list(items: list[str], conj: str = "and") -> str:
    """['a', 'b', 'c'] -> 'a, b or c' (no comma before the conjunction)."""
    if not items:
        return "none"
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} {conj} {items[-1]}"


def format_label(kind: str, slug: Any) -> str:
    return LABELS.get(kind, {}).get(str(slug), humanize(slug))


def format_value(field: str, value: Any, conj: str = "or") -> str:
    """Format a criterion value for a student.

    conj: 'or' for expected lists (any one is fine), 'and' for the student's own lists.
    """
    if value is None:
        return "not provided"
    if isinstance(value, (list, tuple, set, frozenset)):
        items = sorted(value, key=str) if isinstance(value, (set, frozenset)) else list(value)
        return format_list([format_value(field, item, conj) for item in items], conj)
    if isinstance(value, bool):
        return "yes" if value else "no"

    kind = value_kind(field)
    if kind == "date":
        return format_date(value)
    if kind == "percent":
        return format_percent(value)
    if kind == "years":
        return format_years(value)
    if kind == "months":
        return format_months(value)
    if kind == "number":
        return format_number(value)
    if kind in LABELS:
        return format_label(kind, value)
    return humanize(value)