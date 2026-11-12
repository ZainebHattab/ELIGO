"""ELIGO ai/ package: the Data & AI pole's functions, called from Django views.

The Development pole calls these and never re-implements their logic.
The four signatures below are the integration contract agreed at G1.
"""
from .generation import generate_cv, generate_letter
from .matching import evaluate_match
from .rag import answer_question

__all__ = ["evaluate_match", "answer_question", "generate_letter", "generate_cv"]
