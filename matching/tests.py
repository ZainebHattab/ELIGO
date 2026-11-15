from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from matching.services import compute_matches
from profiles.models import Profile
from profiles.services import missing_required_fields
from profiles.tests import BASE
from programs.models import EligibilityCriterion
from programs.test_program_dict import make_program, make_scheme

COMPLETE = {**BASE, "date_of_birth": date(2000, 1, 1)}   # real date, not a string


def make_student(email: str, **overrides) -> Profile:
    user = get_user_model().objects.create_user(email=email, password="x")
    return Profile.objects.create(user=user, **{**COMPLETE, **overrides})


def require_field(scheme, code: str, value: str, program=None) -> None:
    """A hard criterion: field_of_study must equal `value`."""
    EligibilityCriterion.objects.create(
        code=code, scope="program" if program else "scheme", scheme=scheme, track="master",
        program=program, field="field_of_study", operator="eq", value=value, strength="hard",
    )


class MatchesAccessTests(TestCase):
    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse("matches"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('matches')}")

    def test_incomplete_profile_shows_message_not_results(self):
        user = get_user_model().objects.create_user(email="empty@example.com", password="x")
        Profile.objects.create(user=user)             # only the model defaults are filled
        self.client.force_login(user)
        response = self.client.get(reverse("matches"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["incomplete"])
        self.assertNotIn("groups", response.context)
        self.assertContains(response, reverse("profile_edit"))

    def test_missing_required_fields_lists_only_empty_ones(self):
        self.assertEqual(missing_required_fields(make_student("full@example.com")), [])
        user = get_user_model().objects.create_user(email="part@example.com", password="x")
        profile = Profile.objects.create(user=user)
        missing = missing_required_fields(profile)
        self.assertIn("date_of_birth", missing)
        self.assertNotIn("nationalities", missing)    # defaults to ["TN"]


class MatchesResultTests(TestCase):
    def setUp(self):
        self.scheme = make_scheme("daad")
        self.eng = make_program(self.scheme, "prg-eng")
        self.maths = make_program(self.scheme, "prg-maths")
        require_field(self.scheme, "X-ENG", "engineering_technology", program=self.eng)
        require_field(self.scheme, "X-MATH", "mathematics_statistics", program=self.maths)

    def statuses(self, client) -> dict[str, str]:
        response = client.get(reverse("matches"))
        self.assertEqual(response.status_code, 200)
        return {
            m.program.slug: m.result["status"]
            for _, items in response.context["groups"] for m in items
        }

    def test_one_eligible_and_one_not_eligible(self):
        self.client.force_login(make_student("a@example.com").user)   # engineering student
        statuses = self.statuses(self.client)
        self.assertEqual(statuses["prg-eng"], "eligible")
        self.assertEqual(statuses["prg-maths"], "not_eligible")

    def test_each_user_sees_only_their_own_profile_results(self):
        a = make_student("a@example.com")
        b = make_student("b@example.com", field_of_study="mathematics_statistics")
        self.client.force_login(a.user)
        self.assertEqual(self.statuses(self.client)["prg-eng"], "eligible")
        self.client.force_login(b.user)
        self.assertEqual(self.statuses(self.client)["prg-eng"], "not_eligible")
        self.assertEqual(self.statuses(self.client)["prg-maths"], "eligible")

    def test_best_status_comes_first_inside_a_scheme(self):
        self.client.force_login(make_student("a@example.com").user)
        (_, items), = self.client.get(reverse("matches")).context["groups"]
        self.assertEqual([m.program.slug for m in items], ["prg-eng", "prg-maths"])

    def test_cycle_notice_only_for_closed_and_not_not_eligible(self):
        profile = make_student("a@example.com")
        by_slug = {m.program.slug: m for m in compute_matches(profile)}
        self.assertFalse(by_slug["prg-eng"].show_cycle_notice)        # cycle open (deadline 2027-01-15)
        self.eng.deadline = date(2020, 1, 1)
        self.eng.save()
        self.maths.deadline = date(2020, 1, 1)
        self.maths.save()
        by_slug = {m.program.slug: m for m in compute_matches(profile)}
        self.assertTrue(by_slug["prg-eng"].show_cycle_notice)         # eligible + closed
        self.assertFalse(by_slug["prg-maths"].show_cycle_notice)      # not eligible + closed