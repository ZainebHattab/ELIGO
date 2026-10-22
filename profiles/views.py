from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import EducationFormSet, LanguageFormSet, ProfileForm
from .models import Profile


@login_required
def profile_edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        education_formset = EducationFormSet(request.POST, instance=profile, prefix="education")
        language_formset = LanguageFormSet(request.POST, instance=profile, prefix="languages")
        if form.is_valid() and education_formset.is_valid() and language_formset.is_valid():
            with transaction.atomic():
                form.save()
                education_formset.save()
                language_formset.save()
            messages.success(request, "Your profile has been saved.")
            return redirect("profile_edit")
    else:
        form = ProfileForm(instance=profile)
        education_formset = EducationFormSet(instance=profile, prefix="education")
        language_formset = LanguageFormSet(instance=profile, prefix="languages")

    return render(request, "profiles/profile_form.html", {
        "form": form,
        "education_formset": education_formset,
        "language_formset": language_formset,
    })
