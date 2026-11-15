from django import forms

from profiles import choices as pc

from .models import OPPORTUNITY_TYPE, TRACK


def _with_all(label: str, choices: list) -> list:
    return [("", label)] + list(choices)


class ProgramFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Search")
    country = forms.ChoiceField(required=False, choices=_with_all("All countries", pc.COUNTRY))
    track = forms.ChoiceField(required=False, choices=_with_all("All levels", TRACK))
    opportunity_type = forms.ChoiceField(required=False, choices=_with_all("All types", OPPORTUNITY_TYPE))
    status = forms.ChoiceField(
        required=False,
        choices=_with_all("Any status", [("open", "Open"), ("upcoming", "Upcoming"), ("closed", "Closed")]),
    )