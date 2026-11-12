import json
from datetime import date

import pytest

from ai.matching.criteria_io import load_criteria_csv
from ai.matching.engine import select_criteria
from ai.matching.match import evaluate_match
from ai.tests.helpers import COMPLETE_PROFILE, CSV_PATH

STATUSES = {"eligible", "partially_eligible", "not_eligible"}
SOURCES = {"scheme", "program"}

PROGRAM = {"slug": "prg-x", "scheme_slug": "daad", "track": "master", "degree_level_offered": "master",
           "deadline": date(2027, 1, 6), "start_date": date(2027, 9, 1)}
STUDENT = {"current_level": "master", "target_degree_level": "master", "languages": [{"language": "en", "cefr_level": "B2"}]}


def crit(id_="T", scope="scheme", field="current_level", operator="gte", value="bachelor", strength="hard"):
    return {"id": id_, "scope": scope, "field": field, "operator": operator, "value": value, "strength": strength}


def match(criteria, profile=STUDENT, program=PROGRAM):
    return evaluate_match(profile, {**program, "criteria": criteria})


def assert_contract(result):
    assert set(result) == {"status", "score", "reasons", "missing"}
    assert result["status"] in STATUSES
    assert isinstance(result["score"], int) and 0 <= result["score"] <= 100
    for reason in result["reasons"]:
        assert set(reason) == {"source", "text"} and reason["source"] in SOURCES and reason["text"]
    for item in result["missing"]:
        assert set(item) == {"source", "field", "text"} and item["source"] in SOURCES and item["field"] and item["text"]
    json.dumps(result)          # plain types only: safe for views, templates and caches


# ---------- contract ----------
def test_contract_with_eligible_failing_and_missing_results():
    for result in (match([crit()]), match([crit(value="phd")]), match([crit(field="year_of_study", operator="eq", value=3)])):
        assert_contract(result)


def test_no_criteria_key_and_empty_inputs_never_crash():
    assert_contract(evaluate_match({}, {}))
    assert_contract(evaluate_match(STUDENT, {k: v for k, v in PROGRAM.items()}))


def test_eligible_result():
    assert match([crit()]) == {"status": "eligible", "score": 100, "reasons": [], "missing": []}


# ---------- reasons and missing carry their source ----------
def test_failed_criteria_become_reasons_with_their_source():
    result = match([crit("S1", value="phd"), crit("P1", scope="program", field="language:en", value="C1")])
    assert result["status"] == "not_eligible"
    assert sorted(r["source"] for r in result["reasons"]) == ["program", "scheme"]


def test_missing_criteria_become_missing_items_with_field_and_source():
    result = match([crit("P1", scope="program", field="months_resident_in_germany", operator="lte", value=15)])
    assert result["status"] == "partially_eligible" and result["reasons"] == []
    assert [(m["source"], m["field"]) for m in result["missing"]] == [("program", "months_resident_in_germany")]


def test_a_missing_soft_criterion_is_not_asked_and_changes_nothing():
    result = match([crit(), crit("S2", field="year_of_study", operator="eq", value=3, strength="soft")])
    assert result["status"] == "eligible" and result["missing"] == []


def test_blocking_reasons_come_first():
    rule = crit("A", field="current_level", operator="eq", value="phd", strength="as_a_rule")
    block = crit("B", field="current_level", operator="gte", value="phd", strength="hard")
    result = match([rule, block])
    assert "gte" in result["reasons"][0]["text"] and "eq" in result["reasons"][1]["text"]


# ---------- target degree level ----------
def test_target_level_matching_passes():
    assert match([])["status"] == "eligible"


def test_target_level_mismatch_is_not_eligible_with_a_program_reason():
    result = match([], profile={**STUDENT, "target_degree_level": "phd"})
    assert result["status"] == "not_eligible"
    assert [r["source"] for r in result["reasons"]] == ["program"]
    assert result["score"] <= 39


def test_unknown_target_level_is_partial_and_asks_for_it():
    result = match([], profile={**STUDENT, "target_degree_level": None})
    assert result["status"] == "partially_eligible"
    assert [(m["source"], m["field"]) for m in result["missing"]] == [("program", "target_degree_level")]


def test_program_without_degree_level_offered_skips_the_target_check():
    program = {k: v for k, v in PROGRAM.items() if k != "degree_level_offered"}
    assert match([], profile={**STUDENT, "target_degree_level": "phd"}, program=program)["status"] == "eligible"


# ---------- real criteria through the public function ----------
needs_csv = pytest.mark.skipif(not CSV_PATH.exists(), reason="copy the engine CSV to ai/matching/data/")
PROFILE = {**COMPLETE_PROFILE, "target_degree_level": "master"}
D01 = {"slug": "prg-d01", "scheme_slug": "daad", "track": "master", "degree_level_offered": "master",
       "deadline": None, "start_date": date(2027, 10, 1)}
E01 = {"slug": "prg-e01", "scheme_slug": "campus_france_eiffel", "track": "master", "degree_level_offered": "master",
       "deadline": date(2027, 1, 6), "start_date": date(2027, 9, 1)}


def real(profile, program):
    criteria = select_criteria(load_criteria_csv(CSV_PATH), program)
    return evaluate_match(profile, {**program, "criteria": criteria})


@needs_csv
def test_real_eiffel_eligible():
    assert real(PROFILE, E01) == {"status": "eligible", "score": 100, "reasons": [], "missing": []}


@needs_csv
def test_real_eiffel_french_dual_national():
    result = real({**PROFILE, "nationalities": ["TN", "FR"]}, E01)
    assert_contract(result)
    assert result["status"] == "not_eligible"
    assert [r["source"] for r in result["reasons"]] == ["scheme"]


@needs_csv
def test_real_daad_without_deadline_asks_for_nothing_the_student_can_give_but_stays_partial():
    result = real(PROFILE, D01)
    assert_contract(result)
    assert result["status"] == "partially_eligible" and 40 <= result["score"] <= 69
    assert [(m["source"], m["field"]) for m in result["missing"]] == [("scheme", "years_since_highest_degree_at_deadline")]


@needs_csv
def test_real_target_mismatch_on_eiffel():
    result = real({**PROFILE, "target_degree_level": "phd"}, E01)
    assert result["status"] == "not_eligible"
    assert [r["source"] for r in result["reasons"]] == ["program"]
