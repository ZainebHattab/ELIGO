from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from . import choices as c


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")

    # Identity and origin
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=2, choices=c.NATIONALITY, default="TN")
    country_of_residence = models.CharField(max_length=10, choices=c.COUNTRY, default="TN")

    # Current studies
    current_level = models.CharField(max_length=30, choices=c.CURRENT_LEVEL, null=True, blank=True)
    year_of_study = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(6)]
    )
    expected_graduation = models.DateField(null=True, blank=True)
    enrollment_mode = models.CharField(max_length=30, choices=c.ENROLLMENT_MODE, null=True, blank=True)
    institution_type = models.CharField(max_length=30, choices=c.INSTITUTION_TYPE, null=True, blank=True)
    institution_country = models.CharField(max_length=10, choices=c.COUNTRY, default="TN")
    class_rank_percentile = models.DecimalField(
        "class rank (top X %)", max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(100)],
    )
    field_of_study = models.CharField(max_length=30, choices=c.FIELD_OF_STUDY, null=True, blank=True)
    subfield = models.CharField(max_length=30, choices=c.SUBFIELD, null=True, blank=True)
    specialization = models.CharField(max_length=100, blank=True)

    # Degrees already obtained
    highest_degree = models.CharField(max_length=30, choices=c.DEGREE_LEVEL, null=True, blank=True)
    first_degree_date = models.DateField(null=True, blank=True)
    highest_degree_date = models.DateField(null=True, blank=True)

    # Marks
    gpa_value = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)]
    )
    gpa_scale = models.CharField(max_length=5, choices=c.GPA_SCALE, null=True, blank=True)

    # Experience and awards
    work_experience_months = models.PositiveIntegerField(null=True, blank=True)
    work_experience_hours_post_degree = models.PositiveIntegerField(null=True, blank=True)
    previous_awards = models.JSONField(default=list, blank=True)

    # Target
    target_degree_level = models.CharField(max_length=30, choices=c.TARGET_DEGREE_LEVEL, null=True, blank=True)

    # Used only for ranking and generation (matching: false)
    interests = models.JSONField(default=list, blank=True)
    target_countries = models.JSONField(default=list, blank=True)
    target_opportunity_types = models.JSONField(default=list, blank=True)
    consent_ai_processing = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.email}"


class Education(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="education")
    degree = models.CharField(max_length=120)
    institution = models.CharField(max_length=150)
    year = models.PositiveSmallIntegerField(
        "graduation year", validators=[MinValueValidator(1990), MaxValueValidator(2040)]
    )

    class Meta:
        ordering = ["-year"]

    def __str__(self):
        return f"{self.degree} - {self.institution} ({self.year})"


class LanguageSkill(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="languages")
    language = models.CharField(max_length=10, choices=c.LANGUAGE)
    cefr_level = models.CharField("level", max_length=10, choices=c.CEFR)
    certificate_type = models.CharField(max_length=20, choices=c.CERTIFICATE_TYPE, null=True, blank=True)
    certificate_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    certificate_date = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["profile", "language"], name="unique_language_per_profile"),
        ]

    def __str__(self):
        return f"{self.get_language_display()} ({self.cefr_level})"
