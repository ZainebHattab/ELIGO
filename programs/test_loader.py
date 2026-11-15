import tempfile
from pathlib import Path

from django.test import TestCase

from .loader import load_all
from .models import EligibilityCriterion, Program

SCHEMES = """schemes:
  - {slug: sh, name: SH, operator: SH, type: scholarship, tracks: [phd], source_url: "https://x.org", date_checked: 2026-11-10}
"""
PROGRAMS = """programs:
  - slug: prg-s07
    name: PhD
    scheme_slug: sh
    country: HU
    opportunity_type: scholarship
    track: phd
    degree_level_offered: phd
    deadline_rounds: [2026-11-15]
    source_url: "https://x.org"
    date_checked: 2026-11-09
    required_documents: ["Doc A"]
criteria:
  - {id: PRG-X, program_slug: prg-s07, scope: program, scheme_slug: sh, track: phd,
     field: field_of_study, operator: eq, value: engineering_technology, strength: hard}
"""
HEADER = "id,scheme_slug,track,scope,applies_to,field,operator,value,strength,cycle,to_verify,note,source,date_checked\n"
CSV = HEADER + (
    'S-P01,sh,phd,scheme,all programs of scheme+track,nationalities,contains,"""TN""",hard,c,no,,src,2026-10-25\n'
    'S-P10,sh,phd,program,all programs of scheme+track,supervisor_status,neq,"""none""",hard,c,no,,src,2026-10-25\n'
    'E-P05,sh,phd,program,variant:36m,previous_awards,not_contains,"""x""",hard,c,no,,src,2026-10-25\n'
)


class LoaderTests(TestCase):
    def _load(self):
        tmp = Path(tempfile.mkdtemp())
        paths = []
        for name, text in (("s.yaml", SCHEMES), ("p.yaml", PROGRAMS), ("c.csv", CSV)):
            (tmp / name).write_text(text, encoding="utf-8")
            paths.append(tmp / name)
        return load_all(*paths)

    def test_loads_and_attaches(self):
        report = self._load()
        self.assertEqual((report.schemes, report.programs, report.criteria, report.documents), (1, 1, 3, 1))
        self.assertEqual(len(report.warnings), 1)
        s10 = EligibilityCriterion.objects.get(code="S-P10")
        self.assertEqual((s10.scope, s10.program.slug), ("program", "prg-s07"))
        self.assertIsNone(EligibilityCriterion.objects.get(code="S-P01").program)
        self.assertEqual(s10.value, "none")

    def test_rerun_creates_no_duplicates(self):
        self._load()
        self._load()
        self.assertEqual(EligibilityCriterion.objects.count(), 3)
        self.assertEqual(Program.objects.count(), 1)
        self.assertEqual(Program.objects.get().documents.count(), 1)
        self.assertEqual(Program.objects.get().deadline_rounds, ["2026-11-15"])