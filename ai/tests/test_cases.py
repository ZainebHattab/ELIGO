"""Task 7: runs every case of ai/data/test_profiles.yaml through the engine.

Expected values were worked out BY HAND from the CSV and programs_draft.yaml.
Two layers are checked (no text of reasons, task 6 will change it):
  - public layer  (evaluate_match): status, score band, sources of reasons, `source:field` of missing
  - engine layer  (evaluate_criteria): ids of the failed criteria (skipped when `failing` is null)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from ai.matching.criteria_io import load_criteria_csv
from ai.matching.criterion import Outcome
from ai.matching.engine import evaluate_criteria, select_criteria
from ai.matching.match import evaluate_match
from ai.tests.helpers import CSV_PATH

DATA = Path(__file__).resolve().parents[1] / "data"
CASES_PATH = DATA / "test_profiles.yaml"
PROGRAMS_PATH = DATA / "programs_draft.yaml"

# Guaranteed by scoring.py: the status picks the band.
BANDS = {"eligible": (70, 100), "partially_eligible": (40, 69), "not_eligible": (0, 39)}

pytestmark = pytest.mark.skipif(
    not (CSV_PATH.exists() and CASES_PATH.exists() and PROGRAMS_PATH.exists()),
    reason="copy the CSV, test_profiles.yaml and programs_draft.yaml to ai/data/",
)


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _load_all() -> tuple[dict, list[dict], dict, list[dict]]:
    """base profiles, cases, programs by slug, all criteria (CSV + program-level)."""
    if not (CSV_PATH.exists() and CASES_PATH.exists() and PROGRAMS_PATH.exists()):
        return {}, [], {}, []
    suite, drafts = _load_yaml(CASES_PATH), _load_yaml(PROGRAMS_PATH)
    programs = {p["slug"]: p for p in drafts["programs"]}
    criteria = load_criteria_csv(CSV_PATH) + list(drafts["criteria"])
    return suite["base_profiles"], suite["cases"], programs, criteria


BASES, CASES, PROGRAMS, CRITERIA = _load_all()


def _case_id(case: dict[str, Any]) -> str:
    return case["id"] + (" to_verify" if case.get("to_verify") else "")


def _build(case: dict[str, Any]) -> tuple[dict, dict, list]:
    profile = {**BASES[case["base"]], **case.get("set", {})}          # null in YAML = None = unknown
    program = {**PROGRAMS[case["program"]], **case.get("program_set", {})}
    return profile, program, select_criteria(CRITERIA, program)


# ---------- the suite itself must be sound ----------
def test_case_ids_are_unique_and_point_to_real_things():
    ids = [c["id"] for c in CASES]
    assert len(ids) == len(set(ids)), "duplicate case id"
    for case in CASES:
        assert case["base"] in BASES, f"{case['id']}: unknown base"
        assert case["program"] in PROGRAMS, f"{case['id']}: unknown program"


def test_every_expected_failing_id_exists_in_the_selected_criteria():
    """Catches a typo such as PRG-D02-EN written differently in the YAML."""
    for case in CASES:
        _, _, criteria = _build(case)
        known = {c["id"] for c in criteria}
        for wanted in case["expect"].get("failing") or []:
            assert wanted in known, f"{case['id']}: {wanted} is not a selected criterion"


# ---------- the cases ----------
@pytest.mark.parametrize("case", CASES, ids=_case_id)
def test_case(case: dict[str, Any]) -> None:
    expect = case["expect"]
    profile, program, criteria = _build(case)

    # public layer: what Shaima's pages receive
    result = evaluate_match(profile, {**program, "criteria": criteria})
    assert result["status"] == expect["status"]
    low, high = BANDS[expect["status"]]
    assert isinstance(result["score"], int) and low <= result["score"] <= high
    assert {r["source"] for r in result["reasons"]} == set(expect["reasons_from"])
    assert {f"{m['source']}:{m['field']}" for m in result["missing"]} == set(expect["missing"])

    # engine layer: ids of the failed criteria (null = not checked, e.g. TARGET-LEVEL cases)
    if expect.get("failing") is not None:
        evaluation = evaluate_criteria(criteria, profile, program)
        failed = {r.id for r in evaluation.results if r.outcome is Outcome.FAIL}
        assert failed == set(expect["failing"])