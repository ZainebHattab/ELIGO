from django.db import models
from datetime import date
from django.utils import timezone

class FundingScheme(models.Model):
    TYPE_CHOICES = [
        ("scholarship", "Scholarship"),
        ("internship", "Internship"),
    ]

    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    operator = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    tracks = models.JSONField(default=list, blank=True)
    source_url = models.URLField(blank=True)
    date_checked = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Program(models.Model):
    DEADLINE_BASIS_CHOICES = [
        ("confirmed", "Confirmed"),
        ("estimated", "Estimated"),
    ]

    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    operator = models.CharField(max_length=255)
    institution = models.CharField(max_length=255)
    country = models.CharField(max_length=50)
    opportunity_type = models.CharField(max_length=50)
    scheme = models.ForeignKey(
        FundingScheme, on_delete=models.CASCADE, related_name="programs"
    )
    track = models.CharField(max_length=100, blank=True)
    degree_level_offered = models.CharField(max_length=50, blank=True)
    field_of_study = models.CharField(max_length=100, blank=True)
    language_of_instruction = models.CharField(max_length=20, blank=True)
    application_route = models.CharField(max_length=255, blank=True)
    cohort = models.CharField(max_length=50, blank=True)

    # Dates: "deadline" is the FUNDING deadline, "host_deadline" is the host/internal one
    deadline = models.DateField(null=True, blank=True)
    host_deadline = models.DateField(null=True, blank=True)
    opening_date = models.DateField(null=True, blank=True)
    deadline_rounds = models.JSONField(default=list, blank=True)
    next_expected_deadline = models.DateField(null=True, blank=True)
    deadline_basis = models.CharField(
        max_length=20, choices=DEADLINE_BASIS_CHOICES, blank=True
    )
    start_date = models.DateField(null=True, blank=True)

    source_url = models.URLField(blank=True)
    date_checked = models.DateField(null=True, blank=True)
    declarations = models.JSONField(default=list, blank=True)

    # NOTE: there is NO stored "status" field. It is computed later.

    class Meta:
        ordering = ["name"]
        
# ---- Computed cycle status (never stored) ----

    @staticmethod
    def _to_date(value):
        """Accept a date or an ISO string like '2027-01-15'."""
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except (TypeError, ValueError):
            return None

    def _round_dates(self):
        rounds = [self._to_date(r) for r in (self.deadline_rounds or [])]
        return sorted(r for r in rounds if r)

    def gate_date(self, today=None):
        """The date that closes the current cycle, or None if unknown.

        - With deadline_rounds: the next round on or after today.
        - Otherwise: the earliest of deadline and host_deadline.
        """
        today = today or timezone.localdate()
        rounds = self._round_dates()
        if rounds:
            upcoming = [r for r in rounds if r >= today]
            return upcoming[0] if upcoming else None
        candidates = [d for d in (self.deadline, self.host_deadline) if d]
        return min(candidates) if candidates else None

    def cycle_status(self, today=None):
        """One of: 'unknown', 'not_open_yet', 'open', 'closed'."""
        today = today or timezone.localdate()
        if self.opening_date and today < self.opening_date:
            return "not_open_yet"
        gate = self.gate_date(today)
        if gate is None:
            # No usable date. With rounds, all rounds have passed.
            return "closed" if self._round_dates() else "unknown"
        return "open" if today <= gate else "closed"

    @property
    def status(self):
        return self.cycle_status()

    def __str__(self):
        return self.name


class EligibilityCriterion(models.Model):
    SCOPE_CHOICES = [
        ("scheme", "Scheme"),
        ("program", "Program"),
    ]
    STRENGTH_CHOICES = [
        ("hard", "Hard"),
        ("as_a_rule", "As a rule"),
        ("soft", "Soft"),
    ]

    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)
    scheme = models.ForeignKey(
        FundingScheme, on_delete=models.CASCADE, related_name="criteria"
    )
    track = models.CharField(max_length=100, blank=True)
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="criteria",
        null=True,
        blank=True,
    )
    field = models.CharField(max_length=255)
    operator = models.CharField(max_length=50)
    value = models.JSONField()
    strength = models.CharField(max_length=20, choices=STRENGTH_CHOICES)
    cycle = models.CharField(max_length=50, blank=True)
    to_verify = models.BooleanField(default=False)
    source_note = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Eligibility criteria"

    def __str__(self):
        return f"{self.scope}: {self.field} {self.operator}"


class RequiredDocument(models.Model):
    scheme = models.ForeignKey(
        FundingScheme,
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
        blank=True,
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    note = models.TextField(blank=True)

    def __str__(self):
        return self.name