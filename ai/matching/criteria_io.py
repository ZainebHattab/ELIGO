"""Reads the engine CSV export. In the CSV, `value` is JSON text ('"C1"', '6', '["TN"]') and to_verify is yes/no."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def load_criteria_csv(path: str | Path) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8", newline="") as handle:
        return [
            {**row, "value": json.loads(row["value"]), "to_verify": row["to_verify"] == "yes"}
            for row in csv.DictReader(handle)
        ]
