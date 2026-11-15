from django.urls import reverse
from accounts.models import User
from django.test import TestCase

from datetime import date

from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import EligibilityCriterion, FundingScheme, Program


def make_scheme() -> FundingScheme:
    return FundingScheme.objects.create(
        slug="s", name="S", operator="op", type="scholarship", tracks=["master"],
        source_url="https://example.org", date_checked=date(2026, 11, 14),
    )


def make_program(scheme: FundingScheme, **kw) -> Program:
    return Program.objects.create(
        slug=kw.pop("slug", "p"), name="P", country="DE", opportunity_type="scholarship",
        scheme=scheme, track="master", degree_level_offered="master",
        source_url="https://example.org", date_checked=date(2026, 11, 14), **kw,
    )


class CycleStatusTests(TestCase):
    def setUp(self):
        self.scheme = make_scheme()
        self.today = date(2026, 11, 14)

    def test_unknown_without_dates(self):
        self.assertEqual(make_program(self.scheme).cycle_status(self.today), "unknown")

    def test_open_and_closed(self):
        p = make_program(self.scheme, deadline=date(2026, 11, 14))
        self.assertEqual(p.cycle_status(self.today), "open")
        self.assertEqual(p.cycle_status(date(2026, 11, 15)), "closed")

    def test_earliest_deadline_wins(self):
        p = make_program(self.scheme, deadline=date(2027, 1, 15), host_deadline=date(2026, 11, 1))
        self.assertEqual(p.cycle_status(self.today), "closed")

    def test_rounds(self):
        p = make_program(self.scheme, deadline_rounds=["2026-11-15", "2027-05-15"])
        self.assertEqual(p.cycle_status(date(2026, 12, 1)), "open")
        self.assertEqual(p.cycle_status(date(2027, 6, 1)), "closed")

    def test_upcoming(self):
        p = make_program(self.scheme, opening_date=date(2026, 12, 1), deadline=date(2027, 1, 15))
        self.assertEqual(p.cycle_status(self.today), "upcoming")


class CriterionConstraintTests(TestCase):
    def setUp(self):
        self.scheme = make_scheme()
        self.program = make_program(self.scheme)

    def _create(self, **kw):
        defaults = dict(code="X-1", scheme=self.scheme, track="master", field="age_at_deadline",
                        operator="lte", value=30, strength="hard")
        with transaction.atomic():
            return EligibilityCriterion.objects.create(**{**defaults, **kw})

    def test_scheme_scope_rejects_program(self):
        with self.assertRaises(IntegrityError):
            self._create(scope="scheme", program=self.program)

    def test_program_scope_requires_program(self):
        with self.assertRaises(IntegrityError):
            self._create(scope="program")

    def test_no_duplicate_scheme_criterion(self):
        self._create(scope="scheme")
        with self.assertRaises(IntegrityError):
            self._create(scope="scheme")
class AdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="a@x.org", password="pw-12345-pw")
        self.client.force_login(self.admin)
        self.scheme = make_scheme()
        self.program = make_program(self.scheme)

    def test_pages_load(self):
        urls = [
            reverse("admin:programs_fundingscheme_changelist"),
            reverse("admin:programs_program_changelist"),
            reverse("admin:programs_eligibilitycriterion_changelist"),
            reverse("admin:programs_fundingscheme_change", args=[self.scheme.pk]),
            reverse("admin:programs_program_change", args=[self.program.pk]),
        ]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_program_inline_sets_hidden_fields(self):
        data = {
            "slug": self.program.slug, "name": "P", "operator": "", "institution": "",
            "country": "DE", "opportunity_type": "scholarship", "scheme": self.scheme.pk,
            "track": "master", "degree_level_offered": "master", "field_of_study": "",
            "language_of_instruction": "", "application_route": "", "cohort": "",
            "deadline_rounds": "[]", "declarations": "[]", "deadline_basis": "",
            "source_url": "https://example.org", "date_checked": "2026-11-14",
            "criteria-TOTAL_FORMS": "1", "criteria-INITIAL_FORMS": "0",
            "criteria-MIN_NUM_FORMS": "0", "criteria-MAX_NUM_FORMS": "1000",
            "criteria-0-id": "", "criteria-0-program": self.program.pk,
            "criteria-0-code": "X-1", "criteria-0-field": "age_at_deadline",
            "criteria-0-operator": "lte", "criteria-0-value": "30", "criteria-0-strength": "hard",
            "documents-TOTAL_FORMS": "0", "documents-INITIAL_FORMS": "0",
            "documents-MIN_NUM_FORMS": "0", "documents-MAX_NUM_FORMS": "1000",
        }
        url = reverse("admin:programs_program_change", args=[self.program.pk])
        self.assertEqual(self.client.post(url, data).status_code, 302)
        crit = EligibilityCriterion.objects.get(code="X-1")
        self.assertEqual((crit.scope, crit.scheme, crit.track, crit.program),
                         ("program", self.scheme, "master", self.program))