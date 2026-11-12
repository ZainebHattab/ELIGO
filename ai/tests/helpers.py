from datetime import date
from pathlib import Path
CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "ELIGO_criteria_engine_export (1).csv"
COMPLETE_PROFILE = {
    "date_of_birth": date(2000, 1, 1), "current_level": "engineering_cycle", "highest_degree": "bachelor",
    "first_degree_date": date(2022, 7, 1), "highest_degree_date": date(2022, 7, 1), "expected_graduation": date(2027, 6, 30),
    "enrollment_mode": "full_time", "institution_type": "public", "institution_country": "TN", "year_of_study": 3,
    "class_rank_percentile": 10, "field_of_study": "engineering_technology", "gpa_value": 15, "gpa_scale": 20,
    "post_bac_years_completed": 3, "hungarian_status_flags": [], "joint_supervision_agreement": False,
    "master_started_in_germany": False, "months_resident_in_germany": 0, "nationalities": ["TN"],
    "pfe_agreement": True, "previous_awards": [], "rejected_applications": [], "supervisor_status": "confirmed",
    "work_study_contract": False,
}