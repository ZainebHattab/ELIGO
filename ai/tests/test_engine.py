from datetime import date

import pytest

from ai.matching.criteria_io import load_criteria_csv
from ai.matching.criterion import Outcome
from ai.matching.engine import Status, applies_to_program, combine_statuses, evaluate_program, select_criteria
from ai.tests.helpers import COMPLETE_PROFILE, CSV_PATH

E, P, N = Status.ELIGIBLE, Status.PARTIALLY_ELIGIBLE, Status.NOT_ELIGIBLE

PROGRAM = {"slug": "prg-x", "scheme_slug": "daad", "track": "master", "deadline": date(2027, 1, 6), "start_date": date(2027, 9, 1)}


def crit(id_="T", scope="scheme", field="current_level", operator="gte", value="bachelor", strength="hard", **extra):
    return {"id": id_, "scope": scope, "scheme_slug": "daad", "track": "master", "field": field,
            "operator": operator, "value": value, "strength": strength, **extra}


# ---------- selection ----------
def test_scheme_and_track_must_match():
    assert applies_to_program(crit(), PROGRAM)
    assert not applies_to_program(crit(scheme_slug="campus_france_eiffel"), PROGRAM)
    assert not applies_to_program(crit(track="phd"), PROGRAM)


def test_program_slug_selects_one_program_only():
    assert applies_to_program(crit(scope="program", program_slug="PRG-X"), PROGRAM)       # case does not matter
    assert not applies_to_program(crit(scope="program", program_slug="prg-y"), PROGRAM)


def test_applies_to_variants_and_slug_lists():
    assert applies_to_program(crit(applies_to="all programs of scheme+track"), PROGRAM)
    assert applies_to_program(crit(applies_to="variant:36m"), {**PROGRAM, "variant": "36m"})
    assert not applies_to_program(crit(applies_to="variant:36m"), PROGRAM)
    assert not applies_to_program(crit(applies_to="variant:36m"), {**PROGRAM, "variant": "12_18m"})
    assert applies_to_program(crit(applies_to="prg-a, PRG-X"), PROGRAM)
    assert not applies_to_program(crit(applies_to="programs whose doctoral school requires it"), PROGRAM)


def test_select_criteria_filters_a_list():
    criteria = [crit("A"), crit("B", track="phd"), crit("C", scope="program", program_slug="prg-x")]
    assert [c["id"] for c in select_criteria(criteria, PROGRAM)] == ["A", "C"]


# ---------- combination ----------
@pytest.mark.parametrize("scheme, program, expected", [
    (E, E, E), (E, P, P), (P, E, P), (P, P, P), (E, N, N), (N, E, N), (P, N, N), (N, N, N),
])
def test_status_needs_both_sides(scheme, program, expected):
    assert combine_statuses(scheme, program) is expected


# ---------- evaluate_program ----------
STUDENT = {"current_level": "master", "field_of_study": "engineering_technology", "languages": [{"language": "en", "cefr_level": "B2"}]}


def test_empty_program_level_list_works():
    result = evaluate_program([crit()], STUDENT, PROGRAM)
    assert result.status is E and result.program_status is E and result.scheme_status is E


def test_no_criteria_at_all_is_eligible():
    assert evaluate_program([], STUDENT, PROGRAM).status is E


def test_passes_scheme_but_fails_program_hard():
    english = crit("P1", scope="program", program_slug="prg-x", field="language:en", value="C1")
    result = evaluate_program([crit(), english], STUDENT, PROGRAM)
    assert (result.scheme_status, result.program_status, result.status) == (E, N, N)


def test_fails_scheme_but_passes_program():
    result = evaluate_program(
        [crit(value="phd"), crit("P1", scope="program", program_slug="prg-x", field="language:en", value="B2")], STUDENT, PROGRAM)
    assert (result.scheme_status, result.program_status, result.status) == (N, E, N)


def test_program_as_a_rule_fail_is_partial():
    rule = crit("P1", scope="program", program_slug="prg-x", field="field_of_study", operator="eq",
                value="mathematics_statistics", strength="as_a_rule")
    assert evaluate_program([crit(), rule], STUDENT, PROGRAM).status is P


def test_missing_data_gives_partial_never_eligible_or_crash():
    missing = crit("S2", field="months_resident_in_germany", operator="lte", value=15)
    result = evaluate_program([crit(), missing], STUDENT, PROGRAM)
    assert result.status is P
    assert [r.outcome for r in result.results] == [Outcome.PASS, Outcome.MISSING]


def test_soft_fail_does_not_change_status():
    soft = crit("S3", field="field_of_study", operator="eq", value="natural_sciences", strength="soft")
    assert evaluate_program([crit(), soft], STUDENT, PROGRAM).status is E


def test_results_list_scheme_first_then_program():
    program_rule = crit("P1", scope="program", program_slug="prg-x")
    ids = [r.id for r in evaluate_program([program_rule, crit("S1")], STUDENT, PROGRAM).results]
    assert ids == ["S1", "P1"]


def test_criteria_of_another_program_are_ignored():
    other = crit("P9", scope="program", program_slug="prg-other", value="phd")
    assert evaluate_program([crit(), other], STUDENT, PROGRAM).status is E


# ---------- real criteria (copy the CSV to ai/matching/data/) ----------
needs_csv = pytest.mark.skipif(not CSV_PATH.exists(), reason="copy the engine CSV to ai/matching/data/")

D01 = {"slug": "prg-d01", "scheme_slug": "daad", "track": "master", "deadline": None, "start_date": date(2027, 10, 1)}
E01 = {"slug": "prg-e01", "scheme_slug": "campus_france_eiffel", "track": "master", "deadline": date(2027, 1, 6), "start_date": date(2027, 9, 1)}


@needs_csv
def test_real_daad_without_deadline_is_partial_because_d_m02_is_missing():
    result = evaluate_program(load_criteria_csv(CSV_PATH), COMPLETE_PROFILE, D01)
    assert result.status is P and result.program_status is E     # D01 has no program criteria
    assert [r.id for r in result.results if r.outcome is Outcome.MISSING] == ["D-M02"]


@needs_csv
def test_real_daad_with_a_deadline_would_be_eligible():
    result = evaluate_program(load_criteria_csv(CSV_PATH), COMPLETE_PROFILE, {**D01, "deadline": date(2026, 11, 15)})
    assert result.status is E


@needs_csv
def test_real_eiffel_french_dual_national_is_not_eligible():
    profile = {**COMPLETE_PROFILE, "nationalities": ["TN", "FR"]}
    result = evaluate_program(load_criteria_csv(CSV_PATH), profile, E01)
    assert result.status is N
    assert [r.id for r in result.results if r.impact.value == "blocks"] == ["E-M01"]


@needs_csv
def test_real_eiffel_complete_profile_with_english_b2_program_rule():
    english = {"id": "E-P01", "scope": "program", "scheme_slug": "campus_france_eiffel", "track": "master",
               "program_slug": "prg-e01", "field": "language:en", "operator": "gte", "value": "B2", "strength": "hard"}
    criteria = load_criteria_csv(CSV_PATH) + [english]
    b2 = {**COMPLETE_PROFILE, "languages": [{"language": "en", "cefr_level": "B2"}]}
    assert evaluate_program(criteria, b2, E01).status is E
    b1 = {**COMPLETE_PROFILE, "languages": [{"language": "en", "cefr_level": "B1"}]}
    result = evaluate_program(criteria, b1, E01)
    assert (result.scheme_status, result.program_status, result.status) == (E, N, N)
