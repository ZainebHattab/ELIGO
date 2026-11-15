"""Bridge between the Django models and Zaineb's evaluate_match()."""
from django.db.models import Q

from ai.matching import evaluate_match

from .models import EligibilityCriterion

REQUIRED_PROFILE_FIELDS = (
    "date_of_birth",
    "current_level",
    "field_of_study",
    "gpa_value",
    "gpa_scale",
    "target_degree_level",
)


def missing_profile_fields(profile):
    """Names of the key profile fields the student has not filled yet."""
    return [f for f in REQUIRED_PROFILE_FIELDS if getattr(profile, f, None) in (None, "")]


def profile_to_dict(profile):
    """Turn a Profile instance into the plain dict the engine expects."""
    data = {}
    for field in profile._meta.concrete_fields:
        if field.name in ("id", "user", "updated_at"):
            continue
        value = getattr(profile, field.name)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        elif hasattr(value, "as_tuple"):  # Decimal
            value = float(value)
        data[field.name] = value

    # v0.6 expects a list of nationalities. Temporary until Profile is updated.
    data["nationalities"] = [profile.nationality] if profile.nationality else []

    data["languages"] = [
        {
            "language": s.language,
            "cefr_level": s.cefr_level,
            "certificate_type": s.certificate_type,
            "certificate_score": float(s.certificate_score) if s.certificate_score is not None else None,
            "certificate_date": s.certificate_date.isoformat() if s.certificate_date else None,
        }
        for s in profile.languages.all()
    ]
    return data


def criteria_for_program(program):
    """Scheme-level criteria (matching track) plus this program's own criteria."""
    rows = EligibilityCriterion.objects.filter(
        Q(scope="scheme", scheme=program.scheme, track__in=["", program.track])
        | Q(scope="program", program=program)
    )
    return [
        {
            "id": row.pk,
            "scope": row.scope,
            "field": row.field,
            "operator": row.operator,
            "value": row.value,
            "strength": row.strength,
            "to_verify": row.to_verify,
        }
        for row in rows
    ]


def program_to_dict(program):
    return {
        "slug": program.slug,
        "name": program.name,
        "operator": program.operator,
        "institution": program.institution,
        "country": program.country,
        "opportunity_type": program.opportunity_type,
        "track": program.track,
        "degree_level_offered": program.degree_level_offered,
        "field_of_study": program.field_of_study,
        "language_of_instruction": program.language_of_instruction,
        "deadline": program.deadline.isoformat() if program.deadline else None,
        "host_deadline": program.host_deadline.isoformat() if program.host_deadline else None,
        "criteria": criteria_for_program(program),
    }


def match_program(profile_dict, program):
    return evaluate_match(profile_dict, program_to_dict(program))