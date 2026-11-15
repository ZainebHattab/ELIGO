from datetime import date

from django.test import TestCase

from ai.matching.match import evaluate_match
from programs.models import EligibilityCriterion, FundingScheme, Program
from programs.services import build_program_dict


def make_scheme(slug: str) -> FundingScheme:
    return FundingScheme.objects.create(
        slug=slug, name=slug.upper(), operator=slug, type="scholarship",
        tracks=["master", "phd"], source_url="https://example.org", date_checked=date(2026, 11, 1),
    )


def make_program(scheme: FundingScheme, slug: str, track: str = "master") -> Program:
    return Program.objects.create(
        slug=slug, name=slug, scheme=scheme, track=track, degree_level_offered=track,
        country="DE", opportunity_type="scholarship", deadline=date(2027, 1, 15),
        start_date=date(2027, 9, 1), source_url="https://example.org", date_checked=date(2026, 11, 1),
    )


def make_criterion(scheme, code, track="master", program=None, **extra) -> EligibilityCriterion:
    return EligibilityCriterion.objects.create(
        code=code, scope="program" if program else "scheme", scheme=scheme, track=track, program=program,
        field=extra.get("field", "gpa_percent"), operator="gte", value=extra.get("value", 60),
        strength="hard",
    )


class BuildProgramDictTests(TestCase):
    def setUp(self):
        self.daad = make_scheme("daad")
        self.prog = make_program(self.daad, "prg-d02")

    def ids(self) -> list[str]:
        return [c["id"] for c in build_program_dict(self.prog)["criteria"]]

    def test_scheme_and_own_program_criteria_are_included(self):
        make_criterion(self.daad, "D-M01")
        make_criterion(self.daad, "PRG-D02-EN", program=self.prog)
        self.assertEqual(self.ids(), ["D-M01", "PRG-D02-EN"])  # scheme first

    def test_other_scheme_track_and_program_are_excluded(self):
        other_scheme = make_scheme("sh")
        other_program = make_program(self.daad, "prg-d01")
        make_criterion(self.daad, "D-M01")
        make_criterion(other_scheme, "S-M01")                                  # other scheme
        make_criterion(self.daad, "D-P01", track="phd")                        # other track
        make_criterion(self.daad, "PRG-D01-EN", program=other_program)         # other program
        self.assertEqual(self.ids(), ["D-M01"])

    def test_record_keys_the_engine_needs(self):
        data = build_program_dict(self.prog)
        self.assertEqual(data["degree_level_offered"], "master")
        self.assertEqual(data["deadline"], date(2027, 1, 15))
        self.assertEqual(data["start_date"], date(2027, 9, 1))
        self.assertNotIn("status", data)

    def test_criterion_dict_shape(self):
        make_criterion(self.daad, "D-M01", value=60)
        crit = build_program_dict(self.prog)["criteria"][0]
        self.assertEqual(set(crit), {"id", "scope", "field", "operator", "value", "strength", "to_verify", "cycle"})
        self.assertEqual(crit["value"], 60)

    def test_engine_accepts_the_dict(self):
        ok = evaluate_match({"target_degree_level": "master"}, build_program_dict(self.prog))
        self.assertEqual(ok["status"], "eligible")
        wrong = evaluate_match({"target_degree_level": "phd"}, build_program_dict(self.prog))
        self.assertEqual(wrong["status"], "not_eligible")