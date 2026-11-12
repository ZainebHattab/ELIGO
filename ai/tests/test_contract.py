"""Contract tests: the stubs must already respect the output shapes agreed at G1.
The same tests must keep passing when the real engine replaces the stub."""
import inspect

import pytest

import ai
from ai import answer_question, evaluate_match, generate_cv, generate_letter
from ai.matching import sample_result
from ai.types import SOURCES, STATUSES

PROFILE = {"nationalities": ["TN"], "gpa_percent": 78}
PROGRAM = {"id": 1, "slug": "demo"}


def _check_match(result):
    assert set(result) == {"status", "score", "reasons", "missing"}
    assert result["status"] in STATUSES
    assert isinstance(result["score"], int) and 0 <= result["score"] <= 100
    for r in result["reasons"]:
        assert r["source"] in SOURCES and isinstance(r["text"], str) and r["text"]
    for m in result["missing"]:
        assert m["source"] in SOURCES and m["field"] and m["text"]


def test_four_signatures_are_importable_from_package():
    assert set(ai.__all__) == {"evaluate_match", "answer_question", "generate_letter", "generate_cv"}


def test_signatures_match_the_contract():
    assert list(inspect.signature(evaluate_match).parameters) == ["profile", "program"]
    assert list(inspect.signature(answer_question).parameters) == ["question", "program_id"]
    assert list(inspect.signature(generate_letter).parameters) == ["profile", "program"]
    assert list(inspect.signature(generate_cv).parameters) == ["profile", "program"]


def test_evaluate_match_default_shape():
    _check_match(evaluate_match(PROFILE, PROGRAM))


@pytest.mark.parametrize("status", STATUSES)
def test_all_three_badges_available_for_ui_testing(status):
    result = evaluate_match(PROFILE, {**PROGRAM, "_stub_status": status})
    _check_match(result)
    assert result["status"] == status


def test_missing_or_empty_data_never_crashes():
    _check_match(evaluate_match({}, {}))
    _check_match(evaluate_match(PROFILE, {"_stub_status": "garbage"}))


def test_results_are_independent_copies():
    a = evaluate_match(PROFILE, PROGRAM)
    a["reasons"].append({"source": "scheme", "text": "mutated"})
    assert len(evaluate_match(PROFILE, PROGRAM)["reasons"]) != len(a["reasons"])
    assert sample_result()["reasons"] == evaluate_match(PROFILE, PROGRAM)["reasons"]


def test_answer_question_shape_and_dont_know_state():
    r = answer_question("What is the deadline?", None)
    assert set(r) == {"answer", "citations", "found"}
    assert r["found"] is False and r["citations"] == []
    assert set(answer_question("x", 3)) == {"answer", "citations", "found"}


def test_generation_shapes():
    assert set(generate_letter(PROFILE, PROGRAM)) == {"text"}
    cv = generate_cv(PROFILE, PROGRAM)
    assert set(cv) == {"sections"} and all({"title", "lines"} <= set(s) for s in cv["sections"])
