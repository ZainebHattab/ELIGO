from django.contrib import admin

from .models import Education, LanguageSkill, Profile


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0


class LanguageSkillInline(admin.TabularInline):
    model = LanguageSkill
    extra = 0


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user", "current_level", "field_of_study", "highest_degree",
        "target_degree_level", "consent_ai_processing", "updated_at",
    )
    list_filter = (
        "current_level", "field_of_study", "highest_degree", "target_degree_level",
        "enrollment_mode", "institution_type", "consent_ai_processing",
    )
    search_fields = ("user__email", "specialization")
    list_select_related = ("user",)
    raw_id_fields = ("user",)
    readonly_fields = ("updated_at",)
    inlines = [EducationInline, LanguageSkillInline]

    fieldsets = (
        ("Account", {"fields": ("user", "updated_at")}),
        ("Identity", {"fields": ("date_of_birth", "nationalities", "country_of_residence")}),
        ("Germany and Hungary", {"fields": (
            "months_resident_in_germany", "master_started_in_germany", "hungarian_status_flags",
        )}),
        ("Current studies", {"fields": (
            "current_level", "year_of_study", "post_bac_years_completed", "expected_graduation",
            "enrollment_mode", "institution_type", "institution_country", "class_rank_percentile",
            "field_of_study", "subfield", "specialization",
        )}),
        ("Degrees and marks", {"fields": (
            "highest_degree", "first_degree_date", "highest_degree_date", "phd_start_date",
            "gpa_value", "gpa_scale",
        )}),
        ("Experience and awards", {"fields": (
            "work_experience_months", "work_experience_hours_post_degree",
            "previous_awards", "rejected_applications",
        )}),
        ("Application readiness", {"fields": (
            "work_study_contract", "supervisor_status", "joint_supervision_agreement", "pfe_agreement",
        )}),
        ("Goals", {"fields": (
            "target_degree_level", "target_countries", "target_opportunity_types",
            "interests", "consent_ai_processing",
        )}),
    )
