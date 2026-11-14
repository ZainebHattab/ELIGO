from django.shortcuts import get_object_or_404, render

from .models import Program


def program_list(request):
    programs = Program.objects.select_related("scheme").order_by("name")

    country = request.GET.get("country", "")
    opportunity_type = request.GET.get("opportunity_type", "")
    track = request.GET.get("track", "")

    if country:
        programs = programs.filter(country=country)
    if opportunity_type:
        programs = programs.filter(opportunity_type=opportunity_type)
    if track:
        programs = programs.filter(track=track)

    def distinct_values(field):
        return (
            Program.objects.exclude(**{field: ""})
            .values_list(field, flat=True)
            .distinct()
            .order_by(field)
        )

    context = {
        "programs": programs,
        "countries": distinct_values("country"),
        "opportunity_types": distinct_values("opportunity_type"),
        "tracks": distinct_values("track"),
        "selected": {
            "country": country,
            "opportunity_type": opportunity_type,
            "track": track,
        },
    }
    return render(request, "programs/program_list.html", context)


def program_detail(request, slug):
    program = get_object_or_404(
        Program.objects.select_related("scheme"), slug=slug
    )
    context = {
        "program": program,
        "documents": program.documents.all(),
        "scheme_documents": program.scheme.documents.all(),
    }
    return render(request, "programs/program_detail.html", context)