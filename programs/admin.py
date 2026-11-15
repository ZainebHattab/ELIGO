from django.contrib import admin

from .models import (
    EligibilityCriterion,
    FundingScheme,
    Program,
    RequiredDocument,
)


class SchemeCriterionInline(admin.TabularInline):
    """Criteria shown under a FundingScheme (scheme-level rules)."""
    model = EligibilityCriterion
    fk_name = "scheme"
    extra = 0
    # Program-level criteria are managed from the Program page, so hide them here
    exclude = ("program",)
    verbose_name = "scheme criterion"
    verbose_name_plural = "scheme criteria"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(scope="scheme")


class ProgramCriterionInline(admin.TabularInline):
    """Criteria shown under a Program (program-level rules)."""
    model = EligibilityCriterion
    fk_name = "program"
    extra = 0
    verbose_name = "program criterion"
    verbose_name_plural = "program criteria"


class SchemeDocumentInline(admin.TabularInline):
    model = RequiredDocument
    fk_name = "scheme"
    extra = 0
    exclude = ("program",)


class ProgramDocumentInline(admin.TabularInline):
    model = RequiredDocument
    fk_name = "program"
    extra = 0
    exclude = ("scheme",)


@admin.register(FundingScheme)
class FundingSchemeAdmin(admin.ModelAdmin):
    list_display = ("name", "operator", "type", "date_checked")
    list_filter = ("type", "operator")
    search_fields = ("name", "slug", "operator")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [SchemeCriterionInline, SchemeDocumentInline]


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "institution",
        "country",
        "scheme",
        "track",
        "deadline",
        "host_deadline",
        "deadline_basis",
    )
    list_filter = ("country", "opportunity_type", "scheme", "track", "deadline_basis")
    search_fields = ("name", "slug", "institution")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProgramCriterionInline, ProgramDocumentInline]


@admin.register(EligibilityCriterion)
class EligibilityCriterionAdmin(admin.ModelAdmin):
    list_display = ("field", "operator", "value", "strength", "scope", "scheme", "program", "to_verify")
    list_filter = ("scope", "strength", "scheme", "to_verify")
    search_fields = ("field", "source_note")


@admin.register(RequiredDocument)
class RequiredDocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "scheme", "program")
    search_fields = ("name",)