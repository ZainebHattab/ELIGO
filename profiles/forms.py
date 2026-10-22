from datetime import date
from decimal import Decimal

from django import forms
from django.forms import inlineformset_factory

from . import choices as c
from .models import Education, LanguageSkill, Profile


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                widget.attrs["class"] = "form-check-input"
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"
            else:
                widget.attrs["class"] = "form-control"


def date_widget():
    return forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")

def shift_years(years):
    """Today shifted by a number of years (negative = in the past)."""
    today = date.today()
    try:
        return today.replace(year=today.year + years)
    except ValueError:  # 29 February
        return today.replace(year=today.year + years, day=28)
class CommaSeparatedListField(forms.CharField):
    """Free text list (e.g. interests): 'AI, robotics' is stored as ['AI', 'robotics']."""

    def prepare_value(self, value):
        return ", ".join(value) if isinstance(value, list) else value

    def to_python(self, value):
        value = super().to_python(value)
        return [v.strip() for v in value.split(",") if v.strip()] if value else []


class ProfileForm(BootstrapMixin, forms.ModelForm):
    REQUIRED = (
        "date_of_birth", "country_of_residence", "current_level", "enrollment_mode",
        "institution_type", "institution_country", "field_of_study", "highest_degree",
        "target_degree_level",
    )

    previous_awards = forms.MultipleChoiceField(
        choices=c.PREVIOUS_AWARDS, widget=forms.CheckboxSelectMultiple, required=False,
        help_text="Awards you already received or currently hold.",
    )
    target_countries = forms.MultipleChoiceField(
        choices=c.TARGET_COUNTRY, widget=forms.CheckboxSelectMultiple, required=False,
    )
    target_opportunity_types = forms.MultipleChoiceField(
        choices=c.OPPORTUNITY_TYPE, widget=forms.CheckboxSelectMultiple, required=False,
    )
    interests = CommaSeparatedListField(required=False, help_text="Separate with commas.")

    class Meta:
        model = Profile
        fields = [
            "date_of_birth", "country_of_residence",
            "current_level", "year_of_study", "expected_graduation", "enrollment_mode",
            "institution_type", "institution_country", "class_rank_percentile",
            "field_of_study", "subfield", "specialization",
            "highest_degree", "first_degree_date", "highest_degree_date", "gpa_value", "gpa_scale",
            "work_experience_months", "work_experience_hours_post_degree", "previous_awards",
            "target_degree_level", "target_countries", "target_opportunity_types", "interests",
            "consent_ai_processing",
        ]
        widgets = {
            "date_of_birth": date_widget(),
            "expected_graduation": date_widget(),
            "first_degree_date": date_widget(),
            "highest_degree_date": date_widget(),
        }
        labels = {
            "consent_ai_processing": "I agree that my profile data is processed by AI features (letter, CV, assistant)",
            "first_degree_date": "Date of your first degree",
            "highest_degree_date": "Date of your highest degree",
        }
        help_texts = {
            "class_rank_percentile": "Self-declared: 20 means top 20% of your class (between 0.01 and 100). Unverified.",
            "highest_degree": "Highest degree already completed (e.g. licence while in the engineering cycle).",
            "current_level": "What you are enrolled in now.",
            "subfield": "Only needed for programs restricted to a sub-field.",
            "expected_graduation": "Only if you are currently enrolled.",
            "first_degree_date": "When you completed your first university degree (e.g. your licence). Leave empty if none yet.",
            "highest_degree_date": "When you completed your highest degree. Same date as above if it is your only degree.",
        }

    sections = [
        ("Identity", ["date_of_birth", "country_of_residence"]),
        ("Current studies", [
            "current_level", "year_of_study", "expected_graduation", "enrollment_mode",
            "institution_type", "institution_country", "class_rank_percentile",
            "field_of_study", "subfield", "specialization",
        ]),
        ("Degrees and marks", ["highest_degree", "first_degree_date", "highest_degree_date", "gpa_value", "gpa_scale"]),
        ("Experience and awards", ["work_experience_months", "work_experience_hours_post_degree", "previous_awards"]),
        ("Goals", ["target_degree_level", "target_countries", "target_opportunity_types", "interests", "consent_ai_processing"]),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.REQUIRED:
            self.fields[name].required = True

    def grouped_fields(self):
        return [(title, [self[name] for name in names]) for title, names in self.sections]

    def clean(self):
        data = super().clean()
        today = date.today()

        # GPA: a value needs a scale and cannot exceed it
        value, scale = data.get("gpa_value"), data.get("gpa_scale")
        if value is not None and not scale:
            self.add_error("gpa_scale", "Choose the scale of your GPA.")
        elif value is not None and value > Decimal(scale):
            self.add_error("gpa_value", f"The GPA cannot be higher than {scale}.")

        # Date of birth: realistic age
        birth = data.get("date_of_birth")
        if birth and birth > shift_years(-15):
            self.add_error("date_of_birth", "You must be at least 15 years old.")
        elif birth and birth < shift_years(-70):
            self.add_error("date_of_birth", "Please check your date of birth.")

        # Expected graduation: from today to 8 years ahead
        graduation = data.get("expected_graduation")
        if graduation and not (today <= graduation <= shift_years(8)):
            self.add_error("expected_graduation", "Enter a date between today and 8 years from now.")

        # Degree dates: already obtained, so not in the future, and in a logical order
        first, highest = data.get("first_degree_date"), data.get("highest_degree_date")
        for name, d in (("first_degree_date", first), ("highest_degree_date", highest)):
            if d and d > today:
                self.add_error(name, "A degree you already hold cannot be dated in the future (use expected graduation for a degree in progress).")
            elif d and birth and (d - birth).days < 15 * 365:
                self.add_error(name, "This date is too close to your date of birth.")
        if first and highest and highest < first:
            self.add_error("highest_degree_date", "The highest degree cannot be dated before the first degree.")

        # Same date when the first degree is the highest one
        if data.get("highest_degree") == "bachelor" and data.get("first_degree_date") and not data.get("highest_degree_date"):
            data["highest_degree_date"] = data["first_degree_date"]
        return data


class EducationForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Education
        fields = ["degree", "institution", "year"]


class LanguageSkillForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = LanguageSkill
        fields = ["language", "cefr_level", "certificate_type", "certificate_score", "certificate_date"]
        widgets = {"certificate_date": date_widget()}
    def clean_certificate_date(self):
        value = self.cleaned_data.get("certificate_date")
        if value and value > date.today():
            raise forms.ValidationError("The certificate date cannot be in the future.")
        return value

EducationFormSet = inlineformset_factory(Profile, Education, form=EducationForm, extra=0, can_delete=True)
LanguageFormSet = inlineformset_factory(Profile, LanguageSkill, form=LanguageSkillForm, extra=0, can_delete=True)