"""Settings read from environment variables (see .env.example). No secret is stored in code.

The embedding model, the LLM and the vector store are not chosen yet (Sprint 1 leftover,
needed for Sprint 3). Until then these values stay empty and nothing in Sprint 2 uses them.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

try:  # optional: load a local .env file when python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    llm_model: str
    llm_api_key: str
    embedding_model: str
    database_url: str
    rag_top_k: int
    rag_min_score: float
    llm_timeout_seconds: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        llm_provider=os.environ.get("LLM_PROVIDER", ""),
        llm_model=os.environ.get("LLM_MODEL", ""),
        llm_api_key=os.environ.get("LLM_API_KEY", ""),
        embedding_model=os.environ.get("EMBEDDING_MODEL", ""),
        database_url=os.environ.get("DATABASE_URL", ""),
        rag_top_k=int(os.environ.get("RAG_TOP_K", "5")),
        rag_min_score=float(os.environ.get("RAG_MIN_SCORE", "0.0")),
        llm_timeout_seconds=int(os.environ.get("LLM_TIMEOUT_SECONDS", "30")),
    )
