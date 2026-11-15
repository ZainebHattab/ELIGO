"""G3: every case of ai/data/test_profiles.yaml, run through the web app's own code path."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from ai.matching.criterion import Outcome
from ai.matching.engine import evaluate_criteria
from ai.matching.match import evaluate_match
from matching.services import compute_matches
from profiles.models import LanguageSkill, Profile
from profiles.services import profile_to_dict
from programs.loader import load_all
from programs.services import build_program_dict
from programs.models import Program

DATA = Path(settings.BASE_DIR) / "ai" / "data"
BANDS = {"eligible": (70, 100), "partially_eligible": (40, 69), "not_eligible": (0, 39)}


def _load_suite() -> dict[str, Any]:
    with open(DATA / "test_profiles.yaml", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _save_profile(email: str, values: dict[str, Any]) -> Profile:
    """YAML profile -> saved Profile row. `languages` become LanguageSkill rows."""
    values = dict(values)
    languages = values.pop("languages", [])
    if values.get("gpa_scale") is not None:
        values["gpa_scale"] = str(values["gpa_scale"])        # the database stores text
    user = get_user_model().objects.create_user(email=email, password="x")
    profile = Profile.objects.create(user=user, **values)
    for skill in languages:
        LanguageSkill.objects.create(profile=profile, **skill)
    return profile


class G3Tests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        load_all(DATA / "schemes_draft.yaml", DATA / "programs_draft.yaml", DATA / "ELIGO_criteria_engine_export.csv")
        cls.suite = _load_suite()

    def _result(self, profile: Profile, case: dict[str, Any]) -> tuple[dict, dict, dict]:
        """(public result, profile dict, program dict) for one case."""
        slug, program_set = case["program"], case.get("program_set") or {}
        profile_data = profile_to_dict(profile)
        program_data = {**build_program_dict(Program.objects.get(slug=slug)), **program_set}
        if program_set:      # what-if on a program field: the engine is called directly
            return evaluate_match(profile_data, program_data), profile_data, program_data
        match = next(m for m in compute_matches(profile) if m.program.slug == slug)
        return match.result, profile_data, program_data

    def _check(self, case: dict[str, Any], index: int) -> None:
        values = {**self.suite["base_profiles"][case["base"]], **case.get("set", {})}
        profile = _save_profile(f"g3-{index}@example.com", values)
        expect = case["expect"]
        result, profile_data, program_data = self._result(profile, case)

        self.assertEqual(result["status"], expect["status"])
        low, high = BANDS[expect["status"]]
        self.assertTrue(low <= result["score"] <= high, f"score {result['score']} outside {low}-{high}")
        self.assertEqual({r["source"] for r in result["reasons"]}, set(expect["reasons_from"]))
        self.assertEqual({f"{m['source']}:{m['field']}" for m in result["missing"]}, set(expect["missing"]))

        if expect.get("failing") is not None:
            evaluation = evaluate_criteria(program_data["criteria"], profile_data, program_data)
            failed = {r.id for r in evaluation.results if r.outcome is Outcome.FAIL}
            self.assertEqual(failed, set(expect["failing"]))

    def test_all_cases(self) -> None:
        for index, case in enumerate(self.suite["cases"]):
            with self.subTest(case=case["id"]):
                self._check(case, index)

    def test_the_suite_has_46_cases(self) -> None:
        self.assertEqual(len(self.suite["cases"]), 46)