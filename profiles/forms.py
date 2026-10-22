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
        }
        help_texts = {
            "class_rank_percentile": "Self-declared: 20 means top 20% of your class. Unverified.",
            "highest_degree": "Highest degree already completed (e.g. licence while in the engineering cycle).",
            "current_level": "What you are enrolled in now.",
            "subfield": "Only needed for programs restricted to a sub-field.",
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
        value, scale = data.get("gpa_value"), data.get("gpa_scale")
        if value is not None and not scale:
            self.add_error("gpa_scale", "Choose the scale of your GPA.")
        elif value is not None and value > Decimal(scale):
            self.add_error("gpa_value", f"The GPA cannot be higher than {scale}.")
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


EducationFormSet = inlineformset_factory(Profile, Education, form=EducationForm, extra=1, can_delete=True)
LanguageFormSet = inlineformset_factory(Profile, LanguageSkill, form=LanguageSkillForm, extra=1, can_delete=True)