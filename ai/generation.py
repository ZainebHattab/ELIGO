"""Letter and CV generation (Sprint 4, gate G6). Skeleton only: fixed placeholders."""
from __future__ import annotations

from .types import CvResult, LetterResult

IS_STUB = True


def generate_letter(profile: dict, program: dict) -> LetterResult:
    """Stub: placeholder text in the exact output shape."""
    return {"text": "[Draft letter will appear here once generation is implemented.]"}


def generate_cv(profile: dict, program: dict) -> CvResult:
    """Stub: placeholder sections in the exact output shape."""
    return {
        "sections": [
            {"title": "Education", "lines": ["[To be generated from the profile]"]},
            {"title": "Languages", "lines": ["[To be generated from the profile]"]},
        ]
    }
