"""Turns a saved Profile into the plain dict that the ai/ package reads.

Rules (data dictionary v0.6):
  - None stays None: unknown is never turned into False or 0.
  - False, 0 and [] are known answers and are kept as they are.
  - gpa_scale is stored as text ("20", "4.0", "100") and sent as a number.
"""
from .forms import ProfileForm

REQUIRED_FIELDS = (*ProfileForm.REQUIRED, "nationalities")

MATCHING_FIELDS = [
    "date_of_birth", "nationalities", "country_of_residence",
    "months_resident_in_germany", "master_started_in_germany", "hungarian_status_flags",
    "current_level", "year_of_study", "post_bac_years_completed", "expected_graduation",
    "enrollment_mode", "institution_type", "institution_country", "class_rank_percentile",
    "field_of_study", "subfield",
    "highest_degree", "first_degree_date", "highest_degree_date", "phd_start_date", "gpa_value",
    "work_experience_months", "work_experience_hours_post_degree",
    "previous_awards", "rejected_applications",
    "work_study_contract", "supervisor_status", "joint_supervision_agreement", "pfe_agreement",
    "target_degree_level",
]
GENERATION_FIELDS = [
    "specialization", "interests", "target_countries", "target_opportunity_types", "consent_ai_processing",
]
LIST_FIELDS = {
    "nationalities", "hungarian_status_flags", "previous_awards", "rejected_applications",
    "interests", "target_countries", "target_opportunity_types",
}


def _gpa_scale(value):
    if value in (None, ""):
        return None
    return float(value) if "." in str(value) else int(value)     # "20" -> 20, "4.0" -> 4.0


def profile_to_dict(profile):
    data = {}
    for name in MATCHING_FIELDS + GENERATION_FIELDS:
        value = getattr(profile, name)
        data[name] = list(value) if name in LIST_FIELDS and value is not None else value
    data["gpa_scale"] = _gpa_scale(profile.gpa_scale)
    data["languages"] = [
        {
            "language": s.language, "cefr_level": s.cefr_level,
            "certificate_type": s.certificate_type, "certificate_score": s.certificate_score,
            "certificate_date": s.certificate_date,
        }
        for s in profile.languages.all()
    ]
    data["education_entries"] = [
        {"degree": e.degree, "institution": e.institution, "year": e.year}
        for e in profile.education.all()
    ]
    return data
def missing_required_fields(profile) -> list[str]:
    """Names of required fields that are still empty (None, "" or an empty list)."""
    return [name for name in REQUIRED_FIELDS if getattr(profile, name) in (None, "", [])]
