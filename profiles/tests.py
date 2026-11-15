from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase

from profiles.forms import ProfileForm
from profiles.models import Profile,LanguageSkill
from profiles.services import profile_to_dict
from ai.tests.helpers import COMPLETE_PROFILE
BASE = {
    "date_of_birth": "2000-01-01",
    "nationalities": ["TN"],
    "country_of_residence": "TN",
    "current_level": "engineering_cycle",
    "enrollment_mode": "full_time",
    "institution_type": "public",
    "institution_country": "TN",
    "field_of_study": "engineering_technology",
    "highest_degree": "bachelor",
    "target_degree_level": "master",
}


def make_profile(email="student@example.com"):
    user = get_user_model().objects.create_user(email=email, password="x")
    return Profile.objects.create(user=user)


class ProfileFormTests(TestCase):
    def test_form_saves_and_keeps_lists(self):
        profile = make_profile()
        form = ProfileForm({**BASE, "nationalities": ["TN", "FR"], "hungarian_status_flags": []}, instance=profile)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        profile.refresh_from_db()
        self.assertEqual(profile.nationalities, ["TN", "FR"])
        self.assertEqual(profile.hungarian_status_flags, [])   # [] = known "none", not unknown
        self.assertEqual(profile.target_degree_level, "master")

    def test_required_fields(self):
        for name in ProfileForm.REQUIRED + ("nationalities",):
            with self.subTest(field=name):
                data = {k: v for k, v in BASE.items() if k != name}
                form = ProfileForm(data, instance=make_profile(f"{name}@example.com"))
                self.assertFalse(form.is_valid())
                self.assertIn(name, form.errors)

    def test_tristate_booleans_keep_unknown_yes_and_no_apart(self):
        profile = make_profile()
        # field absent = Unknown
        form = ProfileForm(BASE, instance=profile)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        profile.refresh_from_db()
        self.assertIsNone(profile.work_study_contract)

        # Yes and No
        form = ProfileForm({**BASE, "work_study_contract": "true", "pfe_agreement": "false"}, instance=profile)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        profile.refresh_from_db()
        self.assertIs(profile.work_study_contract, True)
        self.assertIs(profile.pfe_agreement, False)     # False is a real answer, not None

    def test_phd_start_date_rejected_when_not_enrolled_in_phd(self):
        form = ProfileForm({**BASE, "phd_start_date": "2025-09-01"}, instance=make_profile())
        self.assertFalse(form.is_valid())
        self.assertIn("phd_start_date", form.errors)

    def test_phd_start_date_accepted_for_a_phd_student(self):
        data = {**BASE, "current_level": "phd", "highest_degree": "master", "phd_start_date": "2025-09-01"}
        form = ProfileForm(data, instance=make_profile())
        self.assertTrue(form.is_valid(), form.errors)


class Migration0003Tests(TransactionTestCase):
    """Goes back to 0002, creates an old-style row, applies 0003, checks the data migration."""
    before = [("profiles", "0002_alter_profile_class_rank_percentile")]
    after = [("profiles", "0003_profile_v06")]

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())   # leave the test database fully migrated

    def test_old_values_are_converted(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.before)
        old_apps = executor.loader.project_state(self.before).apps
        User = old_apps.get_model("accounts", "User")
        OldProfile = old_apps.get_model("profiles", "Profile")
        user = User.objects.create(email="old@example.com")
        OldProfile.objects.create(
            user=user, nationality="TN",
            target_degree_level="research_internship", field_of_study="humanities_arts",
        )

        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(self.after)
        new_apps = executor.loader.project_state(self.after).apps
        row = new_apps.get_model("profiles", "Profile").objects.get(user__email="old@example.com")
        self.assertEqual(row.nationalities, ["TN"])
        self.assertEqual(row.target_degree_level, "internship")
        self.assertEqual(row.field_of_study, "humanities")
class ProfileToDictTests(TestCase):
    def test_saved_profile_has_the_shape_of_COMPLETE_PROFILE(self):
        user = get_user_model().objects.create_user(email="shape@example.com", password="x")
        fields = {**COMPLETE_PROFILE, "gpa_scale": "20"}          # the database stores text
        profile = Profile.objects.create(user=user, **fields)
        profile.refresh_from_db()                                 # values come back as the database types
        result = profile_to_dict(profile)
        for key, expected in COMPLETE_PROFILE.items():
            with self.subTest(key=key):
                self.assertIn(key, result)
                self.assertEqual(result[key], expected)

    def test_gpa_scale_becomes_a_number(self):
        profile = make_profile("gpa@example.com")
        for stored, expected in (("20", 20), ("4.0", 4.0), ("100", 100), (None, None)):
            profile.gpa_scale = stored
            self.assertEqual(profile_to_dict(profile)["gpa_scale"], expected)

    def test_unknown_stays_none_and_known_falsy_values_are_kept(self):
        profile = make_profile("unknown@example.com")
        profile.pfe_agreement = False
        profile.months_resident_in_germany = 0
        profile.save()
        result = profile_to_dict(profile)
        self.assertIsNone(result["work_study_contract"])          # never answered = unknown
        self.assertIs(result["pfe_agreement"], False)
        self.assertEqual(result["months_resident_in_germany"], 0)
        self.assertEqual(result["previous_awards"], [])

    def test_languages_and_education_are_included(self):
        profile = make_profile("lang@example.com")
        LanguageSkill.objects.create(profile=profile, language="en", cefr_level="B2")
        profile.education.create(degree="Licence", institution="FST", year=2022)
        result = profile_to_dict(profile)
        self.assertEqual(result["languages"][0]["language"], "en")
        self.assertEqual(result["languages"][0]["cefr_level"], "B2")
        self.assertEqual(result["education_entries"][0]["year"], 2022)        