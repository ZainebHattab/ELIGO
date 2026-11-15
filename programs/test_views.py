from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .services import cycle_message
from .tests import make_program, make_scheme


class ProgramViewTests(TestCase):
    def setUp(self):
        self.scheme = make_scheme()
        self.de = make_program(self.scheme, slug="de-p", deadline=date(2099, 1, 1))
        self.fr = make_program(self.scheme, slug="fr-p")
        self.fr.country = "FR"
        self.fr.save()
        self.user = User.objects.create_user(email="u@x.org", password="pw-12345-pw")

    def test_anonymous_can_browse(self):
        for url in (reverse("program_list"), reverse("program_detail", args=["de-p"])):
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_anonymous_sees_register_prompt(self):
        response = self.client.get(reverse("program_detail", args=["de-p"]))
        self.assertContains(response, "Create a free account")

    def test_list_and_filters(self):
        self.client.force_login(self.user)
        url = reverse("program_list")
        self.assertEqual(len(self.client.get(url).context["programs"]), 2)
        self.assertEqual([p.slug for p in self.client.get(url, {"country": "FR"}).context["programs"]], ["fr-p"])
        self.assertEqual([p.slug for p in self.client.get(url, {"status": "open"}).context["programs"]], ["de-p"])

    def test_detail_and_404(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("program_detail", args=["de-p"])).status_code, 200)
        self.assertEqual(self.client.get(reverse("program_detail", args=["nope"])).status_code, 404)


class CycleMessageTests(TestCase):
    def setUp(self):
        self.scheme = make_scheme()
        self.today = date(2026, 11, 14)

    def test_closed_without_next_call(self):
        p = make_program(self.scheme, deadline=date(2026, 1, 1))
        self.assertEqual(cycle_message(p, self.today), "No confirmed next call.")

    def test_closed_with_estimated_next_call(self):
        p = make_program(self.scheme, deadline=date(2026, 1, 1),
                         next_expected_deadline=date(2027, 1, 1), deadline_basis="estimated")
        self.assertIn("expected around 1 January 2027", cycle_message(p, self.today))

    def test_open_estimated(self):
        p = make_program(self.scheme, deadline=date(2027, 1, 15), deadline_basis="estimated")
        self.assertIn("expected around 15 January 2027", cycle_message(p, self.today))

    def test_upcoming_and_unknown(self):
        p = make_program(self.scheme, opening_date=date(2026, 12, 1), deadline=date(2027, 1, 15))
        self.assertIn("1 December 2026", cycle_message(p, self.today))
        self.assertEqual(cycle_message(make_program(self.scheme, slug="u"), self.today), "No deadline published yet.")