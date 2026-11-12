from datetime import date

import pytest

from ai.matching.criteria_io import load_criteria_csv
from ai.matching.criterion import CriterionResult, Impact, Outcome
from ai.matching.engine import Status, evaluate_program
from ai.matching.scoring import BANDS, compute_score, ratio
from ai.matching.test_criterion import COMPLETE_PROFILE, CSV_PATH

E, P, N = Status.ELIGIBLE, Status.PARTIALLY_ELIGIBLE, Status.NOT_ELIGIBLE


def result(strength: str, outcome: Outcome) -> CriterionResult:
    return CriterionResult("T", "scheme", "f", strength, outcome, Impact.NONE, None, False)


PASS, FAIL, MISSING = Outcome.PASS, Outcome.FAIL, Outcome.MISSING


def test_ratio_weights_and_points():
    assert ratio([]) == 1.0
    assert ratio([result("hard", PASS)]) == 1.0
    assert ratio([result("hard", FAIL)]) == 0.0
    assert ratio([result("hard", MISSING)]) == 0.5
    # hard pass (3) + soft fail (0) -> 3 / 4
    assert ratio([result("hard", PASS), result("soft", FAIL)]) == 0.75
    # as_a_rule missing counts 2 * 0.5 = 1 out of 2 + 3
    assert ratio([result("hard", PASS), result("as_a_rule", MISSING)]) == pytest.approx(4 / 5)


def test_eligible_without_failures_scores_100_even_with_no_criteria():
    assert compute_score(E, []) == 100
    assert compute_score(E, [result("hard", PASS), result("soft", PASS)]) == 100


def test_soft_fail_only_lowers_the_score_inside_the_eligible_band():
    score = compute_score(E, [result("hard", PASS), result("soft", FAIL)])
    assert score == 93                        # 70 + 30 * 0.75 = 92.5, rounded half up
    assert 70 <= score < 100


@pytest.mark.parametrize("status, results, expected", [
    (P, [result("hard", PASS), result("hard", MISSING)], 40 + 29 * 0.75),   # 61.75 -> 62
    (N, [result("hard", PASS), result("hard", FAIL)], 20),                  # 39 * 0.5 = 19.5 -> 20
    (N, [result("hard", FAIL)], 0),
])
def test_known_values(status, results, expected):
    assert compute_score(status, results) == round(expected + 1e-9)


def test_a_worse_status_never_scores_higher_than_a_better_one():
    best_not_eligible = compute_score(N, [])               # ratio 1
    worst_partial = compute_score(P, [result("hard", FAIL)])    # ratio 0
    best_partial = compute_score(P, [])
    worst_eligible = compute_score(E, [result("hard", FAIL)])
    assert best_not_eligible < worst_partial
    assert best_partial < worst_eligible
    assert (best_not_eligible, worst_partial, best_partial, worst_eligible) == (39, 40, 69, 70)


def test_bands_cover_0_to_100_without_gap():
    assert BANDS[N][0] + BANDS[N][1] + 1 == BANDS[P][0]
    assert BANDS[P][0] + BANDS[P][1] + 1 == BANDS[E][0]
    assert BANDS[E][0] + BANDS[E][1] == 100


def test_score_is_an_int():
    assert isinstance(compute_score(P, [result("hard", MISSING)]), int)


# ---------- the worked examples on the real criteria ----------
needs_csv = pytest.mark.skipif(not CSV_PATH.exists(), reason="copy the engine CSV to ai/matching/data/")
D01 = {"slug": "prg-d01", "scheme_slug": "daad", "track": "master", "deadline": None, "start_date": date(2027, 10, 1)}
E01 = {"slug": "prg-e01", "scheme_slug": "campus_france_eiffel", "track": "master", "deadline": date(2027, 1, 6), "start_date": date(2027, 9, 1)}
S01 = {"slug": "prg-s01", "scheme_slug": "stipendium_hungaricum", "track": "master", "deadline": date(2027, 1, 15), "start_date": None}


@needs_csv
@pytest.mark.parametrize("profile_changes, program, status, score", [
    ({}, E01, E, 100),
    ({}, D01, P, 67),
    ({}, S01, P, 68),
    ({"nationalities": ["TN", "FR"]}, E01, N, 33),
])
def test_real_examples(profile_changes, program, status, score):
    evaluation = evaluate_program(load_criteria_csv(CSV_PATH), {**COMPLETE_PROFILE, **profile_changes}, program)
    assert evaluation.status is status
    assert compute_score(evaluation.status, evaluation.results) == score
