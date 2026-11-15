from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from programs.loader import load_all

DATA = Path(settings.BASE_DIR) / "ai" / "data"


class Command(BaseCommand):
    help = "Load schemes, programs and criteria. Safe to run several times."

    def add_arguments(self, parser):
        parser.add_argument("--schemes", type=Path, default=DATA / "schemes_draft.yaml")
        parser.add_argument("--programs", type=Path, default=DATA / "programs_draft.yaml")
        parser.add_argument("--csv", type=Path, default=DATA / "ELIGO_criteria_engine_export.csv")

    def handle(self, *args, **opts):
        report = load_all(opts["schemes"], opts["programs"], opts["csv"])
        for w in report.warnings:
            self.stdout.write(self.style.WARNING(w))
        self.stdout.write(self.style.SUCCESS(
            f"{report.schemes} schemes, {report.programs} programs, "
            f"{report.criteria} criteria, {report.documents} documents."
        ))