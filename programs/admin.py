from django.contrib import admin

from .models import EligibilityCriterion, FundingScheme, Program, RequiredDocument


class SchemeCriterionInline(admin.TabularInline):
    model = EligibilityCriterion
    extra = 0
    exclude = ("scope", "program")
    verbose_name_plural = "scheme-level criteria"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(program__isnull=True)


class SchemeDocumentInline(admin.TabularInline):
    model = RequiredDocument
    extra = 0
    exclude = ("program",)
    verbose_name_plural = "scheme-level documents"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(program__isnull=True)


class ProgramCriterionInline(admin.TabularInline):
    model = EligibilityCriterion
    extra = 0
    exclude = ("scope", "scheme", "track")
    verbose_name_plural = "program-level criteria"


class ProgramDocumentInline(admin.TabularInline):
    model = RequiredDocument
    extra = 0
    exclude = ("scheme",)
    verbose_name_plural = "program-level documents"


def _save_inlines(formset, defaults: dict) -> None:
    """Save inline rows, setting the fields hidden from the form."""
    instances = formset.save(commit=False)
    for obj in formset.deleted_objects:
        obj.delete()
    for obj in instances:
        for name, value in defaults.items():
            setattr(obj, name, value)
        obj.save()
    formset.save_m2m()


@admin.register(FundingScheme)
class FundingSchemeAdmin(admin.ModelAdmin):
    list_display = ("name", "operator", "type", "date_checked")
    list_filter = ("type",)
    search_fields = ("name", "slug", "operator")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [SchemeCriterionInline, SchemeDocumentInline]

    def save_formset(self, request, form, formset, change):
        scheme = form.instance
        if formset.model is EligibilityCriterion:
            _save_inlines(formset, {"scope": "scheme", "program": None})
        else:
            _save_inlines(formset, {"program": None})


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "scheme", "country", "track", "deadline", "cycle")
    list_filter = ("scheme", "country", "track", "opportunity_type")
    search_fields = ("name", "slug", "institution")
    list_select_related = ("scheme",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("cycle",)
    inlines = [ProgramCriterionInline, ProgramDocumentInline]

    @admin.display(description="Cycle status")
    def cycle(self, obj: Program) -> str:
        return obj.status if obj.pk else "-"

    def save_formset(self, request, form, formset, change):
        program = form.instance
        if formset.model is EligibilityCriterion:
            _save_inlines(formset, {"scope": "program", "scheme": program.scheme, "track": program.track})
        else:
            _save_inlines(formset, {"scheme": program.scheme})


@admin.register(EligibilityCriterion)
class EligibilityCriterionAdmin(admin.ModelAdmin):
    """Read-mostly overview of all rules, for checking the loader's work."""
    list_display = ("code", "scope", "scheme", "track", "program", "field", "operator", "value", "strength", "to_verify")
    list_filter = ("scope", "scheme", "track", "strength", "to_verify")
    search_fields = ("code", "field")
    list_select_related = ("scheme", "program")
