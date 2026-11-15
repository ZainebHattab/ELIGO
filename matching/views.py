from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from profiles.models import Profile
from profiles.services import missing_required_fields

from .services import compute_matches, group_by_scheme


@login_required
def matches(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    missing = missing_required_fields(profile)
    if missing:
        labels = [str(Profile._meta.get_field(n).verbose_name).capitalize() for n in missing]
        return render(request, "matching/matches.html", {"incomplete": True, "missing_labels": labels})
    return render(request, "matching/matches.html", {"groups": group_by_scheme(compute_matches(profile))})