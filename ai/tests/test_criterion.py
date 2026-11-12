from datetime import date
from pathlib import Path

import pytest

from ai.matching.criterion import Impact, Outcome, evaluate_criterion, impact_of
from ai.matching.criteria_io import load_criteria_csv
from ai.tests.helpers import COMPLETE_PROFILE, CSV_PATH

PROGRAM = {"deadline": date(2027, 1, 6), "start_date": date(2027, 9, 1)}
NO_DEADLINE = {"deadline": None, "start_date": date(2027, 10, 1)}


def crit(**overrides):
    base = {"id": "T-01", "scope": "scheme", "field": "current_level", "operator": "gte", "value": "bachelor", "strength": "hard"}
    return {**base, **overrides}


# ---------- outcome ----------
def test_pass_fail_missing():
    assert evaluate_criterion(crit(), {"current_level": "master"}, PROGRAM).outcome is Outcome.PASS
    assert evaluate_criterion(crit(), {"current_level": "secondary"}, PROGRAM).outcome is Outcome.FAIL
    assert evaluate_criterion(crit(), {"current_level": None}, PROGRAM).outcome is Outcome.MISSING
    assert evaluate_criterion(crit(), {}, PROGRAM).outcome is Outcome.MISSING


def test_result_carries_what_the_reasons_need():
    result = evaluate_criterion(crit(id="D-M01", scope="program", to_verify=True), {"current_level": "secondary"}, PROGRAM)
    assert (result.id, result.source, result.field, result.strength) == ("D-M01", "program", "current_level", "hard")
    assert result.actual == "secondary" and result.to_verify is True
    assert evaluate_criterion(crit(), {}, PROGRAM).actual is None


def test_false_is_a_known_answer_not_missing():
    c = crit(field="master_started_in_germany", operator="eq", value=False)
    assert evaluate_criterion(c, {"master_started_in_germany": False}, PROGRAM).outcome is Outcome.PASS
    assert evaluate_criterion(c, {"master_started_in_germany": True}, PROGRAM).outcome is Outcome.FAIL


# ---------- impact by strength ----------
@pytest.mark.parametrize("outcome, strength, impact", [
    (Outcome.PASS, "hard", Impact.NONE), (Outcome.PASS, "as_a_rule", Impact.NONE), (Outcome.PASS, "soft", Impact.NONE),
    (Outcome.FAIL, "hard", Impact.BLOCKS), (Outcome.FAIL, "as_a_rule", Impact.DOWNGRADES), (Outcome.FAIL, "soft", Impact.NONE),
    (Outcome.MISSING, "hard", Impact.DOWNGRADES), (Outcome.MISSING, "as_a_rule", Impact.DOWNGRADES), (Outcome.MISSING, "soft", Impact.NONE),
])
def test_impact_table(outcome, strength, impact):
    assert impact_of(outcome, strength) is impact


def test_missing_hard_never_blocks():
    result = evaluate_criterion(crit(strength="hard"), {}, PROGRAM)
    assert result.impact is Impact.DOWNGRADES


# ---------- the DAAD case: deadline unknown ----------
def test_deadline_dependent_criterion_is_missing_without_deadline():
    d_m02 = crit(id="D-M02", field="years_since_highest_degree_at_deadline", operator="lte", value=6, strength="as_a_rule")
    profile = {"highest_degree": "bachelor", "highest_degree_date": date(2022, 7, 1)}
    assert evaluate_criterion(d_m02, profile, PROGRAM).outcome is Outcome.PASS
    assert evaluate_criterion(d_m02, profile, NO_DEADLINE).outcome is Outcome.MISSING


def test_language_criterion_on_a_program_with_no_listed_language():
    c = crit(scope="program", field="language:en", value="C1")
    assert evaluate_criterion(c, {"languages": []}, PROGRAM).outcome is Outcome.MISSING
    profile = {"languages": [{"language": "en", "cefr_level": "B2"}]}
    assert evaluate_criterion(c, profile, PROGRAM).outcome is Outcome.FAIL


# ---------- bad criteria are loud ----------
def test_bad_criteria_raise():
    with pytest.raises(ValueError):
        evaluate_criterion(crit(strength="mandatory"), {"current_level": "master"}, PROGRAM)
    with pytest.raises(ValueError):
        evaluate_criterion(crit(scope="both"), {"current_level": "master"}, PROGRAM)
    with pytest.raises(ValueError):
        evaluate_criterion({"id": "X", "scope": "scheme", "field": "current_level"}, {}, PROGRAM)
    with pytest.raises(ValueError):
        evaluate_criterion(crit(operator="almost"), {"current_level": "master"}, PROGRAM)


# ---------- guard on the real 62 criteria ----------
CSV_PATH = Path(__file__).parent / "data" / "ELIGO_criteria_engine_export_1.csv"




@pytest.mark.skipif(not CSV_PATH.exists(), reason="copy the engine CSV to ai/matching/data/ to run this guard")
def test_every_csv_criterion_evaluates_and_none_is_missing_for_a_complete_profile():
    criteria = load_criteria_csv(CSV_PATH)
    assert len(criteria) == 62
    results = [evaluate_criterion(c, COMPLETE_PROFILE, PROGRAM) for c in criteria]
    missing = [r.id for r in results if r.outcome is Outcome.MISSING]
    assert missing == [], f"typo in a field name or gap in the resolver: {missing}"


def test_result_keeps_operator_and_expected_value_for_the_reason_templates():
    result = evaluate_criterion(crit(), {"current_level": "secondary"}, PROGRAM)
    assert (result.operator, result.expected) == ("gte", "bachelor")
