DEGREE_LEVEL = [
    ("secondary", "Secondary (baccalaureate level)"),
    ("bachelor", "Bachelor (licence)"),
    ("engineering_cycle", "Engineering cycle (cycle ingénieur)"),
    ("master", "Master"),
    ("phd", "PhD"),
]
CURRENT_LEVEL = [("none", "Not currently enrolled")] + DEGREE_LEVEL

CEFR = [("A1", "A1"), ("A2", "A2"), ("B1", "B1"), ("B2", "B2"), ("C1", "C1"), ("C2", "C2"), ("native", "Native")]

NATIONALITY = [("TN", "Tunisia")]
COUNTRY = [("TN", "Tunisia"), ("FR", "France"), ("DE", "Germany"), ("CA", "Canada"), ("IT", "Italy"), ("other", "Other")]
TARGET_COUNTRY = [("CA", "Canada"), ("DE", "Germany"), ("FR", "France"), ("GB", "United Kingdom"), ("IT", "Italy"), ("other", "Other")]

ENROLLMENT_MODE = [("full_time", "Full time"), ("part_time", "Part time")]
INSTITUTION_TYPE = [("public", "Public"), ("private", "Private")]

FIELD_OF_STUDY = [
    ("engineering_technology", "Engineering and technology (incl. computer science, data, AI)"),
    ("mathematics_statistics", "Mathematics and statistics"),
    ("natural_sciences", "Natural sciences"),
    ("business_economics", "Business and economics"),
    ("health_medicine", "Health and medicine"),
    ("law_social_sciences", "Law and social sciences"),
    ("humanities_arts", "Humanities and arts"),
    ("other", "Other"),
]
SUBFIELD = [
    ("computer_science", "Computer science"),
    ("data_science_ai", "Data science and AI"),
    ("electrical_electronics", "Electrical and electronics"),
    ("mechanical_industrial", "Mechanical and industrial"),
    ("civil_environmental", "Civil and environmental"),
    ("other_engineering", "Other engineering"),
    ("not_applicable", "Not applicable"),
]

GPA_SCALE = [("20", "Out of 20"), ("4.0", "Out of 4.0"), ("100", "Out of 100")]

PREVIOUS_AWARDS = [
    ("mitacs_globalink", "Mitacs Globalink"),
    ("daad_study_scholarship", "DAAD study scholarship"),
    ("eiffel_master", "Eiffel (master)"),
    ("erasmus_mundus_jm", "Erasmus Mundus Joint Master"),
    ("chevening", "Chevening"),
    ("other_uk_government_scholarship", "Other UK government scholarship"),
    ("french_government_scholarship", "French government scholarship"),
]

TARGET_DEGREE_LEVEL = [("master", "Master"), ("phd", "PhD"), ("research_internship", "Research internship")]
OPPORTUNITY_TYPE = [("scholarship", "Scholarship"), ("internship", "Internship"), ("fellowship", "Fellowship")]

LANGUAGE = [("ar", "Arabic"), ("fr", "French"), ("en", "English"), ("de", "German"), ("es", "Spanish"), ("it", "Italian"), ("other", "Other")]
CERTIFICATE_TYPE = [
    ("ielts", "IELTS"), ("toefl", "TOEFL"), ("toeic", "TOEIC"), ("delf", "DELF"), ("dalf", "DALF"),
    ("tcf", "TCF"), ("tef", "TEF"), ("goethe", "Goethe"), ("testdaf", "TestDaF"), ("other", "Other"),
]