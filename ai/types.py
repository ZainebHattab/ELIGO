"""Shared types and constants for the ai/ package (integration contract, agreed at G1).

Do not change the shape of these without telling the Development pole: their matches
page, chat page and generation forms read these dicts directly.
"""
from __future__ import annotations

from typing import TypedDict

# --- evaluate_match -----------------------------------------------------------------
STATUS_ELIGIBLE = "eligible"
STATUS_PARTIAL = "partially_eligible"
STATUS_NOT_ELIGIBLE = "not_eligible"
STATUSES = (STATUS_ELIGIBLE, STATUS_PARTIAL, STATUS_NOT_ELIGIBLE)

# Every reason and every missing item says where it comes from (Sprint 2 plan, task 5).
SOURCE_SCHEME = "scheme"
SOURCE_PROGRAM = "program"
SOURCES = (SOURCE_SCHEME, SOURCE_PROGRAM)


class _ReasonBase(TypedDict):
    source: str  # "scheme" or "program"
    text: str  # plain language, written for a student


class Reason(_ReasonBase, total=False):
    criterion_id: str  # optional, e.g. "E-M02", for debugging and tests


class _MissingBase(TypedDict):
    source: str  # "scheme" or "program"
    field: str  # dictionary field name, e.g. "gpa_percent"
    text: str  # what the student should fill in, in plain language


class MissingItem(_MissingBase, total=False):
    criterion_id: str


class MatchResult(TypedDict):
    status: str  # one of STATUSES
    score: int  # 0 to 100
    reasons: list[Reason]
    missing: list[MissingItem]


# --- answer_question (Sprint 3, G4) ---------------------------------------------------
class _CitationBase(TypedDict):
    source: str  # document title or file name


class Citation(_CitationBase, total=False):
    page: int | None
    url: str
    snippet: str


class AnswerResult(TypedDict):
    answer: str
    citations: list[Citation]
    found: bool  # False = "I don't know" state


# --- generate_letter / generate_cv (Sprint 4, G6) --------------------------------------
class LetterResult(TypedDict):
    text: str


class CvSection(TypedDict):
    title: str
    lines: list[str]


class CvResult(TypedDict):
    sections: list[CvSection]
