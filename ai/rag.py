"""RAG assistant (Sprint 3, gate G4). Skeleton only: returns the "I don't know" state."""
from __future__ import annotations

from .types import AnswerResult

IS_STUB = True


def answer_question(question: str, program_id: int | None = None) -> AnswerResult:
    """Stub: always the "not found" state, so the chat page can show it."""
    return {
        "answer": "I don't have enough information in the indexed sources to answer this yet.",
        "citations": [],
        "found": False,
    }


def index_source(file_path: str, scheme_slug: str | None = None, program_id: int | None = None) -> dict:
    """Placeholder for G5 (admin upload then indexing). Not part of the four agreed signatures:
    agree its exact shape with the Development pole before Sprint 3."""
    raise NotImplementedError("index_source is planned for Sprint 3 (G5).")
