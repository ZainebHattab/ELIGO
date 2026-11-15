from __future__ import annotations

from datetime import date

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from profiles import choices as pc

TRACK = [("master", "Master"), ("phd", "PhD"), ("internship", "Internship")]
OPPORTUNITY_TYPE = [("scholarship", "Scholarship"), ("internship", "Internship")]
LANGUAGE_OF_INSTRUCTION = [
    ("ar", "Arabic"), ("fr", "French"), ("en", "English"),
    ("de", "German"), ("hu", "Hungarian"), ("other", "Other"),
]
APPLICATION_ROUTE = [
    ("direct", "Direct"), ("via_institution", "Via the institution"),
    ("via_home_university", "Via your home university"), ("via_consortium", "Via a consortium"),
    ("via_sending_partner", "Via a sending partner"), ("via_national_committee", "Via a national committee"),
]
DEADLINE_BASIS = [("confirmed", "Confirmed"), ("estimated", "Estimated")]
OPERATOR = [
    ("eq", "eq"), ("neq", "neq"), ("in", "in"), ("not_in", "not_in"),
    ("gte", "gte"), ("lte", "lte"), ("between", "between"),
    ("contains", "contains"), ("not_contains", "not_contains"), ("contains_any", "contains_any"),
]
STRENGTH = [("hard", "Hard"), ("as_a_rule", "As a rule"), ("soft", "Soft")]
SCOPE = [("scheme", "Scheme"), ("program", "Program")]


class FundingScheme(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    operator = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=OPPORTUNITY_TYPE)
    tracks = models.JSONField(default=list)  # subset of master / phd / internship
    source_url = models.URLField()
    date_checked = models.DateField()

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Program(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    operator = models.CharField(max_length=200, blank=True)
    institution = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=10, choices=pc.COUNTRY)
    opportunity_type = models.CharField(max_length=20, choices=OPPORTUNITY_TYPE)
    scheme = models.ForeignKey(FundingScheme, on_delete=models.PROTECT, related_name="programs")
    track = models.CharField(max_length=20, choices=TRACK)
    degree_level_offered = models.CharField(max_length=20, choices=TRACK)
    field_of_study = models.CharField(max_length=30, choices=pc.FIELD_OF_STUDY, blank=True)
    language_of_instruction = models.CharField(max_length=10, choices=LANGUAGE_OF_INSTRUCTION, blank=True)
    application_route = models.CharField(max_length=30, choices=APPLICATION_ROUTE, blank=True)
    cohort = models.CharField(max_length=50, blank=True)

    # Dates. All optional: a missing date is "unknown", never an error.
    opening_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True, help_text="FUNDING application deadline.")
    host_deadline = models.DateField(null=True, blank=True)
    deadline_rounds = models.JSONField(default=list, blank=True, help_text="ISO dates of alternative rounds.")
    next_expected_deadline = models.DateField(null=True, blank=True)
    deadline_basis = models.CharField(max_length=10, choices=DEADLINE_BASIS, blank=True)
    start_date = models.DateField(null=True, blank=True)

    source_url = models.URLField()
    date_checked = models.DateField()
    declarations = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def cycle_status(self, today: date | None = None) -> str:
        """open / closed / upcoming / unknown, computed (dictionary v0.6, changes 37, 40, 41)."""
        today = today or date.today()
        if self.opening_date and today < self.opening_date:
            return "upcoming"
        if self.deadline_rounds:
            rounds = [date.fromisoformat(d) for d in self.deadline_rounds]
            return "open" if any(r >= today for r in rounds) else "closed"
        dates = [d for d in (self.deadline, self.host_deadline) if d]
        if not dates:
            return "unknown"
        return "open" if today <= min(dates) else "closed"

    @property
    def status(self) -> str:
        return self.cycle_status()


class EligibilityCriterion(models.Model):
    code = models.CharField(max_length=40, help_text="Criterion id from the CSV, e.g. E-P05.")
    scope = models.CharField(max_length=10, choices=SCOPE)
    scheme = models.ForeignKey(FundingScheme, on_delete=models.CASCADE, related_name="criteria")
    track = models.CharField(max_length=20, choices=TRACK)
    program = models.ForeignKey(Program, null=True, blank=True, on_delete=models.CASCADE, related_name="criteria")
    field = models.CharField(max_length=120)
    operator = models.CharField(max_length=20, choices=OPERATOR)
    value = models.JSONField()
    strength = models.CharField(max_length=10, choices=STRENGTH)
    cycle = models.CharField(max_length=50, blank=True)
    to_verify = models.BooleanField(default=False)
    source_note = models.TextField(blank=True)
    source_url = models.URLField(blank=True)
    date_checked = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "eligibility criteria"
        ordering = ["scheme", "track", "code"]
        constraints = [
            models.CheckConstraint(
                condition=(Q(scope="scheme", program__isnull=True) | Q(scope="program", program__isnull=False)),
                name="criterion_scope_matches_program",
            ),
            # Two constraints because NULLs are never equal in PostgreSQL.
            models.UniqueConstraint(
                fields=["code", "scheme", "track", "program"], name="unique_criterion_per_program"
            ),
            models.UniqueConstraint(
                fields=["code", "scheme", "track"],
                condition=Q(program__isnull=True),
                name="unique_scheme_criterion",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} ({self.scope})"


class RequiredDocument(models.Model):
    scheme = models.ForeignKey(FundingScheme, on_delete=models.CASCADE, related_name="documents")
    program = models.ForeignKey(Program, null=True, blank=True, on_delete=models.CASCADE, related_name="documents")
    name = models.CharField(max_length=200)
    note = models.CharField(max_length=300, blank=True, help_text="e.g. legalization, translation.")
    order = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name
# Create your models here.
