"""STUB of evaluate_match(): returns a fixed sample in the exact output shape (G2).

It ignores the profile and the program. It exists so the Development pole can build and
test the matches page before the rule engine is ready (G3). It is replaced by
ai/matching/engine.py at G3; the signature and the output shape do not change.

For UI testing only, a program dict may carry "_stub_status" set to one of
"eligible", "partially_eligible", "not_eligible" to get the other two sample badges.
"""
from __future__ import annotations

import copy
import logging

from ..types import (
    SOURCE_PROGRAM,
    SOURCE_SCHEME,
    STATUS_ELIGIBLE,
    STATUS_NOT_ELIGIBLE,
    STATUS_PARTIAL,
    STATUSES,
    MatchResult,
)

IS_STUB = True
_log = logging.getLogger("ai")
_warned = False

_SAMPLES: dict[str, MatchResult] = {
    STATUS_ELIGIBLE: {
        "status": STATUS_ELIGIBLE,
        "score": 92,
        "reasons": [
            {"source": SOURCE_SCHEME, "text": "You meet the nationality and age conditions of this scholarship."},
            {"source": SOURCE_PROGRAM, "text": "Your field of study and your grades fit this program."},
        ],
        "missing": [],
    },
    STATUS_PARTIAL: {
        "status": STATUS_PARTIAL,
        "score": 64,
        "reasons": [
            {"source": SOURCE_SCHEME, "text": "You meet the nationality and age conditions of this scholarship."},
            {
                "source": SOURCE_PROGRAM,
                "text": "Your grade is below the level this program usually asks for, so your application may be less competitive.",
            },
        ],
        "missing": [
            {
                "source": SOURCE_PROGRAM,
                "field": "language:en.cefr_level",
                "text": "Add your English level to your profile so we can check the language requirement of this program.",
            }
        ],
    },
    STATUS_NOT_ELIGIBLE: {
        "status": STATUS_NOT_ELIGIBLE,
        "score": 18,
        "reasons": [
            {
                "source": SOURCE_SCHEME,
                "text": "This scholarship is only open to students born after the age limit of the current call.",
            },
            {"source": SOURCE_PROGRAM, "text": "This program is outside your field of study."},
        ],
        "missing": [],
    },
}


def sample_result(status: str = STATUS_PARTIAL) -> MatchResult:
    """Return a fresh copy of the fixed sample for one status."""
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}, got {status!r}")
    return copy.deepcopy(_SAMPLES[status])


def evaluate_match(profile: dict, program: dict) -> MatchResult:
    """Stub: fixed sample, same shape as the real engine. Never raises on missing data."""
    global _warned
    if not _warned:
        _log.warning("ai.evaluate_match is a STUB and returns a fixed sample (see ai/matching/stub.py).")
        _warned = True
    wanted = program.get("_stub_status") if isinstance(program, dict) else None
    return sample_result(wanted if wanted in STATUSES else STATUS_PARTIAL)
