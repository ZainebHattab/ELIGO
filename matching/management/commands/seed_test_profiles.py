"""Creates one demo student per case of ai/data/test_profiles.yaml and prints expected vs actual."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from matching.services import compute_matches
from profiles.models import LanguageSkill, Profile

DEMO_DOMAIN = "@demo.eligo"
PASSWORD = "demo-pass-123"
CASES_PATH = Path(settings.BASE_DIR) / "ai" / "data" / "test_profiles.yaml"


def _save_profile(email: str, values: dict[str, Any]) -> Profile:
    values = dict(values)
    languages = values.pop("languages", [])
    if values.get("gpa_scale") is not None:
        values["gpa_scale"] = str(values["gpa_scale"])
    user = get_user_model().objects.create_user(email=email, password=PASSWORD)
    profile = Profile.objects.create(user=user, **values)
    for skill in languages:
        LanguageSkill.objects.create(profile=profile, **skill)
    return profile


class Command(BaseCommand):
    help = "Create (or recreate) the demo students of the test set. Use --clear to only delete them."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--clear", action="store_true", help="Delete the demo students and stop.")

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        get_user_model().objects.filter(email__endswith=DEMO_DOMAIN).delete()   # cascades to profiles
        if options["clear"]:
            self.stdout.write("Demo students deleted.")
            return

        with open(CASES_PATH, encoding="utf-8") as handle:
            suite = yaml.safe_load(handle)

        self.stdout.write(f"{'case':<8} {'expected':<20} {'actual':<20} score  login")
        for case in suite["cases"]:
            values = {**suite["base_profiles"][case["base"]], **case.get("set", {})}
            email = f"{case['id'].lower()}{DEMO_DOMAIN}"
            profile = _save_profile(email, values)
            match = next(m for m in compute_matches(profile) if m.program.slug == case["program"])
            what_if = "*" if case.get("program_set") else " "
            self.stdout.write(
                f"{case['id']:<8} {case['expect']['status']:<20} {match.result['status']:<20} "
                f"{match.result['score']:<5}{what_if} {email}"
            )
        self.stdout.write(f"\nPassword for all: {PASSWORD}")
        self.stdout.write("* = what-if case (a different deadline is used in the tests), so 'actual' can differ here.")