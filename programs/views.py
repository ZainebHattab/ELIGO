from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .forms import ProgramFilterForm
from .models import Program, RequiredDocument
from .services import cycle_message


def program_list(request):
    form = ProgramFilterForm(request.GET or None)
    programs = Program.objects.select_related("scheme")
    status = ""
    if form.is_valid():
        data = form.cleaned_data
        if data["q"]:
            programs = programs.filter(Q(name__icontains=data["q"]) | Q(institution__icontains=data["q"]))
        for name in ("country", "track", "opportunity_type"):
            if data[name]:
                programs = programs.filter(**{name: data[name]})
        status = data["status"]
    items = list(programs)
    if status:
        items = [p for p in items if p.status == status]
    return render(request, "programs/program_list.html", {"form": form, "programs": items})


def program_detail(request, slug: str):
    program = get_object_or_404(Program.objects.select_related("scheme"), slug=slug)
    documents = RequiredDocument.objects.filter(scheme=program.scheme).filter(
        Q(program=program) | Q(program__isnull=True)
    )
    return render(request, "programs/program_detail.html", {
        "program": program,
        "message": cycle_message(program),
        "documents": documents,
    })