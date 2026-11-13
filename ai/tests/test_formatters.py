from datetime import date, datetime
from decimal import Decimal

import pytest

from ai.matching.formatters import (
    FIELD_KIND,
    LABELS,
    LANGUAGE_NAMES,
    format_date,
    format_list,
    format_months,
    format_number,
    format_percent,
    format_value,
    format_years,
    humanize,
    language_name,
    parse_language_field,
    value_kind,
)

# Value lists of dictionary v0.6 (a slug missing here or in LABELS is caught below).
DICTIONARY_SLUGS = {
    "degree": ["none", "secondary", "bachelor", "engineering_cycle", "master", "phd"],
    "cefr": ["A1", "A2", "B1", "B2", "C1", "C2", "native"],
    "country": ["TN", "FR", "DE", "HU", "CA", "IT", "other"],
    "nationality": ["TN", "FR", "HU", "other"],
    "field_of_study": [
        "engineering_technology", "mathematics_statistics", "natural_sciences", "business_economics",
        "health_medicine", "law_social_sciences", "humanities", "arts_music_performing",
        "architecture_design", "other",
    ],
    "enrollment": ["full_time", "part_time"],
    "institution_type": ["public", "private"],
    "supervisor": ["none", "contacted", "confirmed"],
    "award": [
        "mitacs_globalink", "daad_study_scholarship", "eiffel_master", "erasmus_mundus_jm", "chevening",
        "other_uk_government_scholarship", "french_government_scholarship", "eiffel_phd", "daad_doctoral",
        "zuse_school_scholarship", "stipendium_hungaricum_bachelor", "stipendium_hungaricum_master",
        "stipendium_hungaricum_phd", "hungarian_government_scholarship",
    ],
    "hungarian_status": ["stateless", "refugee", "long_term_resident"],
    "target_level": ["master", "phd", "internship"],
}


@pytest.mark.parametrize("value, expected", [
    ("1997-04-01", "1 April 1997"),
    (date(2027, 9, 1), "1 September 2027"),
    (datetime(2027, 12, 31, 10, 30), "31 December 2027"),
    ("not_a_date", "not a date"),
])
def test_format_date(value, expected):
    assert format_date(value) == expected


@pytest.mark.parametrize("value, expected", [
    (20, "20"), (100, "100"), (0, "0"), ("80", "80"),
    (Decimal("2.50"), "2.5"), (2.3333, "2.33"), (3.0, "3"),
])
def test_format_number(value, expected):
    assert format_number(value) == expected


def test_format_percent_years_months():
    assert format_percent(80) == "80%"
    assert format_percent(Decimal("82.50")) == "82.5%"
    assert format_years(1) == "1 year"
    assert format_years(0) == "0 years"
    assert format_years(6) == "6 years"
    assert format_years(2.5) == "2.5 years"
    assert format_months(1) == "1 month"
    assert format_months(15) == "15 months"


@pytest.mark.parametrize("items, conj, expected", [
    ([], "or", "none"),
    (["a"], "or", "a"),
    (["a", "b"], "or", "a or b"),
    (["a", "b", "c"], "and", "a, b and c"),
])
def test_format_list(items, conj, expected):
    assert format_list(items, conj) == expected


@pytest.mark.parametrize("field, value, expected", [
    ("current_level", "engineering_cycle", "engineering cycle (cycle ingénieur)"),
    ("current_level", "none", "not enrolled"),
    ("highest_degree_at_start", "bachelor", "bachelor (licence)"),
    ("language:en", "B2", "B2"),
    ("language:fr", "native", "native speaker"),
    ("language:de.certificate_score", "5.0", "5"),
    ("language:de.certificate_age_years_at_deadline", 3, "3 years"),
    ("target_degree_level", "phd", "a PhD"),
    ("supervisor_status", "contacted", "supervisor contacted"),
    ("institution_country", "TN", "Tunisia"),
    ("enrollment_mode", "full_time", "full time"),
    ("date_of_birth", "1997-04-01", "1 April 1997"),
    ("gpa_percent", 80, "80%"),
    ("class_rank_percentile", Decimal("20.00"), "20%"),
    ("months_resident_in_germany", 15, "15 months"),
    ("currently_studying_in_france", False, "no"),
    ("meets_iaeste_level", True, "yes"),
])
def test_format_value(field, value, expected):
    assert format_value(field, value) == expected


def test_lists_use_the_right_conjunction():
    assert format_value("nationalities", ["TN", "FR"], conj="and") == "Tunisian and French"
    assert format_value("current_level", ["bachelor", "engineering_cycle"]) == (
        "bachelor (licence) or engineering cycle (cycle ingénieur)"
    )
    assert format_value("nationalities", []) == "none"
    assert format_value("previous_awards", {"chevening"}, conj="and") == "Chevening"


def test_missing_and_unknown_values_are_safe():
    assert format_value("age_at_deadline", None) == "not provided"
    assert format_value("some_unknown_field", "some_slug") == "some slug"
    assert humanize("highest_degree_at_start") == "highest degree at start"


def test_language_helpers():
    assert parse_language_field("language:fr") == ("fr", "")
    assert parse_language_field("language:de.certificate_score") == ("de", "certificate_score")
    assert parse_language_field("gpa_percent") is None
    assert language_name("de") == "German"
    assert language_name("xx") == "another language"
    assert value_kind("language:en") == "cefr"
    assert value_kind("language:en.something_new") == "number"


def test_every_dictionary_slug_has_a_label():
    for kind, slugs in DICTIONARY_SLUGS.items():
        for slug in slugs:
            assert slug in LABELS[kind], f"missing label: {kind}/{slug}"


def test_every_field_kind_is_known():
    known = set(LABELS) | {"years", "months", "number", "percent", "date", "yes_no"}
    assert set(FIELD_KIND.values()) <= known


def test_no_underscore_anywhere_in_labels_or_outputs():
    for labels in LABELS.values():
        for text in labels.values():
            assert "_" not in text, text
    for text in LANGUAGE_NAMES.values():
        assert "_" not in text
    for field, kind in FIELD_KIND.items():
        for slug in DICTIONARY_SLUGS.get(kind, []):
            assert "_" not in format_value(field, slug), (field, slug)