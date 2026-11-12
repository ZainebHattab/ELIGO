from datetime import date
from decimal import Decimal

import pytest

from ai.matching.resolver import resolve_field

PROGRAM = {"deadline": date(2027, 1, 6), "start_date": date(2027, 9, 1)}


def student(**overrides):
    base = {
        "date_of_birth": date(1999, 3, 10), "current_level": "engineering_cycle",
        "highest_degree": "bachelor", "first_degree_date": date(2022, 7, 1), "highest_degree_date": date(2022, 7, 1),
        "institution_country": "TN", "field_of_study": "engineering_technology",
        "expected_graduation": date(2027, 6, 30), "previous_awards": [], "gpa_value": Decimal("15.20"), "gpa_scale": "20",
        "languages": [{"language": "en", "cefr_level": "C1", "certificate_score": Decimal("100"), "certificate_date": date(2025, 1, 6)}],
    }
    return {**base, **overrides}


# ---------- plain fields: unknown vs known ----------
def test_plain_field_value_and_unknowns():
    assert resolve_field("current_level", student(), PROGRAM) == "engineering_cycle"
    assert resolve_field("current_level", student(current_level=None), PROGRAM) is None
    assert resolve_field("current_level", {}, PROGRAM) is None           # absent
    assert resolve_field("specialization", student(specialization=""), PROGRAM) is None   # empty text


def test_false_zero_and_empty_list_are_known_values():
    assert resolve_field("work_study_contract", student(work_study_contract=False), PROGRAM) is False
    assert resolve_field("months_resident_in_germany", student(months_resident_in_germany=0), PROGRAM) == 0
    assert resolve_field("previous_awards", student(), PROGRAM) == []


def test_program_fields_are_refused():
    with pytest.raises(ValueError):
        resolve_field("program.field_of_study", student(), PROGRAM)


# ---------- age ----------
def test_age_at_deadline_counts_full_years():
    assert resolve_field("age_at_deadline", student(), PROGRAM) == 27                       # birthday in March
    assert resolve_field("age_at_deadline", student(date_of_birth=date(1999, 1, 6)), PROGRAM) == 28   # birthday on the deadline
    assert resolve_field("age_at_deadline", student(date_of_birth=date(1999, 1, 7)), PROGRAM) == 27   # day after


def test_age_is_unknown_without_birth_date_or_deadline():
    assert resolve_field("age_at_deadline", student(date_of_birth=None), PROGRAM) is None
    assert resolve_field("age_at_deadline", student(), {"deadline": None}) is None         # DAAD case


# ---------- years since degrees ----------
def test_years_since_degree():
    years = resolve_field("years_since_first_degree_at_deadline", student(), PROGRAM)
    assert years == pytest.approx(4.5, abs=0.05)


def test_years_since_degree_zero_when_no_degree_yet_and_unknown_otherwise():
    secondary = student(highest_degree="secondary", first_degree_date=None, highest_degree_date=None)
    assert resolve_field("years_since_highest_degree_at_deadline", secondary, PROGRAM) == 0
    no_date = student(highest_degree="master", highest_degree_date=None)
    assert resolve_field("years_since_highest_degree_at_deadline", no_date, PROGRAM) is None
    assert resolve_field("years_since_highest_degree_at_deadline", student(), {"deadline": None}) is None


# ---------- PhD ----------
def test_phd_years_zero_when_no_phd_started():
    assert resolve_field("years_since_phd_start_at_deadline", student(), PROGRAM) == 0
    assert resolve_field("years_since_phd_start_at_start", student(), PROGRAM) == 0
    assert resolve_field("years_since_phd_start_at_deadline", student(), {"deadline": None}) == 0   # no deadline needed


def test_phd_years_from_start_date_and_unknown_cases():
    phd = student(current_level="phd", phd_start_date=date(2025, 9, 1))
    assert resolve_field("years_since_phd_start_at_start", phd, PROGRAM) == pytest.approx(2.0, abs=0.02)
    assert resolve_field("years_since_phd_start_at_deadline", phd, PROGRAM) == pytest.approx(1.35, abs=0.02)
    assert resolve_field("years_since_phd_start_at_start", student(current_level="phd"), PROGRAM) is None
    assert resolve_field("years_since_phd_start_at_start", student(current_level=None), PROGRAM) is None


def test_phd_starting_after_program_start_is_negative():
    later = student(current_level="phd", phd_start_date=date(2027, 10, 1))
    assert resolve_field("years_since_phd_start_at_start", later, PROGRAM) < 0


# ---------- France / enrolled ----------
@pytest.mark.parametrize("level, country, expected", [
    ("master", "FR", True), ("master", "TN", False), ("none", "FR", False),
    (None, "TN", False), ("none", None, False),      # one known False is enough
    (None, "FR", None), ("master", None, None),      # otherwise unknown
])
def test_currently_studying_in_france(level, country, expected):
    profile = student(current_level=level, institution_country=country)
    assert resolve_field("currently_studying_in_france", profile, PROGRAM) is expected


def test_is_enrolled_or_recent_graduate():
    assert resolve_field("is_enrolled_or_recent_graduate", student(), PROGRAM) is True
    graduate = student(current_level="none", highest_degree_date=date(2026, 7, 1))
    assert resolve_field("is_enrolled_or_recent_graduate", graduate, PROGRAM) is True
    old = student(current_level="none", highest_degree_date=date(2020, 7, 1))
    assert resolve_field("is_enrolled_or_recent_graduate", old, PROGRAM) is False
    unknown = student(current_level="none", highest_degree_date=None, highest_degree="master")
    assert resolve_field("is_enrolled_or_recent_graduate", unknown, PROGRAM) is None


def test_meets_iaeste_level():
    ok = student(post_bac_years_completed=3)
    assert resolve_field("meets_iaeste_level", ok, PROGRAM) is True
    too_early = student(post_bac_years_completed=2, current_level="bachelor")
    assert resolve_field("meets_iaeste_level", too_early, PROGRAM) is False
    masters = student(current_level="master", field_of_study="natural_sciences", post_bac_years_completed=None)
    assert resolve_field("meets_iaeste_level", masters, PROGRAM) is True      # second branch is enough
    assert resolve_field("meets_iaeste_level", student(post_bac_years_completed=None), PROGRAM) is None


# ---------- highest degree at program start ----------
def test_graduating_before_start_counts_as_holding_the_degree():
    assert resolve_field("highest_degree_at_start", student(), PROGRAM) == "engineering_cycle"


def test_graduating_after_start_keeps_the_current_degree():
    late = student(expected_graduation=date(2027, 12, 1))
    assert resolve_field("highest_degree_at_start", late, PROGRAM) == "bachelor"


def test_highest_degree_at_start_cases_that_need_no_dates():
    already = student(current_level="bachelor", highest_degree="master")
    assert resolve_field("highest_degree_at_start", already, {}) == "master"      # not studying higher: dates not needed
    same_rank = student(current_level="master", highest_degree="engineering_cycle")
    assert resolve_field("highest_degree_at_start", same_rank, {}) == "engineering_cycle"


def test_highest_degree_at_start_unknown_cases():
    assert resolve_field("highest_degree_at_start", student(expected_graduation=None), PROGRAM) is None
    assert resolve_field("highest_degree_at_start", student(), {"start_date": None}) is None
    assert resolve_field("highest_degree_at_start", student(highest_degree=None), PROGRAM) is None


# ---------- gpa_percent ----------
def test_gpa_percent_is_exact_for_both_scale_types():
    assert resolve_field("gpa_percent", student(), PROGRAM) == Decimal("76")
    assert resolve_field("gpa_percent", student(gpa_value=Decimal("3.2"), gpa_scale=4.0), PROGRAM) == Decimal("80")
    assert resolve_field("gpa_percent", student(gpa_value=None), PROGRAM) is None
    assert resolve_field("gpa_percent", student(gpa_scale=None), PROGRAM) is None


# ---------- language paths ----------
def test_language_level_score_and_certificate_age():
    assert resolve_field("language:en", student(), PROGRAM) == "C1"
    assert resolve_field("language:en.certificate_score", student(), PROGRAM) == Decimal("100")
    assert resolve_field("language:en.certificate_age_years_at_deadline", student(), PROGRAM) == pytest.approx(2.0, abs=0.01)


def test_language_unknowns():
    assert resolve_field("language:de", student(), PROGRAM) is None                       # not listed
    assert resolve_field("language:en", {}, PROGRAM) is None                              # no languages key
    no_cert = student(languages=[{"language": "en", "cefr_level": "B2"}])
    assert resolve_field("language:en.certificate_score", no_cert, PROGRAM) is None
    assert resolve_field("language:en.certificate_age_years_at_deadline", no_cert, PROGRAM) is None
    assert resolve_field("language:en.certificate_age_years_at_deadline", student(), {"deadline": None}) is None


def test_unknown_language_attribute_is_an_error():
    with pytest.raises(ValueError):
        resolve_field("language:en.colour", student(), PROGRAM)
