from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterator

import yaml
from django.db import transaction

from .models import EligibilityCriterion, FundingScheme, Program, RequiredDocument

ALL_PROGRAMS = "all programs of scheme+track"
SCHEME_FIELDS = ("name", "operator", "type", "tracks", "source_url", "date_checked")
TEXT_FIELDS = (
    "name", "operator", "institution", "country", "opportunity_type", "track",
    "degree_level_offered", "field_of_study", "language_of_instruction",
    "application_route", "cohort", "deadline_basis", "source_url",
)
DATE_FIELDS = (
    "opening_date", "deadline", "host_deadline", "next_expected_deadline",
    "start_date", "date_checked",
)


@dataclass
class LoadReport:
    schemes: int = 0
    programs: int = 0
    criteria: int = 0
    documents: int = 0
    warnings: list[str] = field(default_factory=list)


def _read_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_schemes(data: dict[str, Any], report: LoadReport) -> dict[str, FundingScheme]:
    schemes: dict[str, FundingScheme] = {}
    for row in data["schemes"]:
        if not str(row["source_url"]).startswith("http"):
            raise ValueError(f"Scheme {row['slug']}: source_url is '{row['source_url']}'. Fill a real URL first.")
        obj, _ = FundingScheme.objects.update_or_create(
            slug=row["slug"], defaults={k: row[k] for k in SCHEME_FIELDS}
        )
        schemes[obj.slug] = obj
        report.schemes += 1
    return schemes


def _program_defaults(row: dict[str, Any], scheme: FundingScheme) -> dict[str, Any]:
    defaults: dict[str, Any] = {k: row.get(k) or "" for k in TEXT_FIELDS}
    defaults.update({k: row.get(k) for k in DATE_FIELDS})
    defaults["scheme"] = scheme
    defaults["deadline_rounds"] = [d.isoformat() for d in row.get("deadline_rounds") or []]
    defaults["declarations"] = list(row.get("declarations") or [])
    return defaults


def load_programs(data: dict[str, Any], schemes: dict[str, FundingScheme], report: LoadReport) -> None:
    for row in data["programs"]:
        program, _ = Program.objects.update_or_create(
            slug=row["slug"], defaults=_program_defaults(row, schemes[row["scheme_slug"]])
        )
        names = list(row.get("required_documents") or [])
        for order, name in enumerate(names):
            RequiredDocument.objects.update_or_create(
                program=program, name=name, defaults={"scheme": program.scheme, "order": order}
            )
            report.documents += 1
        program.documents.exclude(name__in=names).delete()
        report.programs += 1


def _yaml_specs(data: dict[str, Any], programs: dict[str, Program]) -> Iterator[tuple[dict[str, Any], Program]]:
    for row in data.get("criteria", []):
        program = programs[row["program_slug"]]
        spec = {
            "code": row["id"], "scheme_slug": row["scheme_slug"], "track": row["track"],
            "field": row["field"], "operator": row["operator"], "value": row["value"],
            "strength": row["strength"], "cycle": row.get("cycle") or "",
            "to_verify": bool(row.get("to_verify")), "source_note": row.get("source_note") or "",
            "date_checked": program.date_checked,
        }
        yield spec, program


def _targets(row: dict[str, str], programs: dict[str, Program]) -> list[Program | None]:
    if row["scope"] == "scheme":
        return [None]
    applies = row["applies_to"]
    if applies == ALL_PROGRAMS:
        return [p for p in programs.values() if p.scheme.slug == row["scheme_slug"] and p.track == row["track"]]
    return [programs[applies]] if applies in programs else []


def _csv_specs(
    path: Path, programs: dict[str, Program], report: LoadReport
) -> Iterator[tuple[dict[str, Any], Program | None]]:
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            targets = _targets(row, programs)
            if not targets:
                report.warnings.append(f"{row['id']}: no program for '{row['applies_to']}', skipped")
                continue
            note = " | ".join(x for x in (row["note"], f"Source: {row['source']}") if x)
            spec = {
                "code": row["id"], "scheme_slug": row["scheme_slug"], "track": row["track"],
                "field": row["field"], "operator": row["operator"], "value": json.loads(row["value"]),
                "strength": row["strength"], "cycle": row["cycle"],
                "to_verify": row["to_verify"].strip().lower() == "yes", "source_note": note,
                "date_checked": date.fromisoformat(row["date_checked"]) if row["date_checked"] else None,
            }
            for target in targets:
                yield spec, target


def _save_criterion(spec: dict[str, Any], target: Program | None, schemes: dict[str, FundingScheme]) -> None:
    keys = {"code": spec["code"], "scheme": schemes[spec["scheme_slug"]], "track": spec["track"], "program": target}
    defaults = {
        "scope": "program" if target else "scheme",
        **{k: spec[k] for k in ("field", "operator", "value", "strength", "cycle", "to_verify", "source_note", "date_checked")},
    }
    EligibilityCriterion.objects.update_or_create(**keys, defaults=defaults)


def load_all(schemes_path: Path, programs_path: Path, csv_path: Path) -> LoadReport:
    report = LoadReport()
    with transaction.atomic():
        schemes = load_schemes(_read_yaml(schemes_path), report)
        data = _read_yaml(programs_path)
        load_programs(data, schemes, report)
        programs = {p.slug: p for p in Program.objects.select_related("scheme")}
        for spec, target in _yaml_specs(data, programs):
            _save_criterion(spec, target, schemes)
            report.criteria += 1
        for spec, target in _csv_specs(csv_path, programs, report):
            _save_criterion(spec, target, schemes)
            report.criteria += 1
    return report