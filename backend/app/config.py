"""Environment-driven settings. Read once per call so tests can override env."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Public demo tokens. Each token maps to exactly one role. Override with TOOLGATE_TOKENS.
DEMO_TOKENS = {"tg-analyst": "analyst", "tg-hr": "hr_admin", "tg-support": "support"}


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    llm_provider: str  # ollama | openai | none
    llm_model: str
    llm_base_url: str
    llm_api_key: str
    embed_provider: str  # hash | ollama
    embed_model: str
    tokens: dict[str, str]
    max_rows: int


def get_settings() -> Settings:
    tokens = json.loads(os.getenv("TOOLGATE_TOKENS", "null")) or DEMO_TOKENS
    return Settings(
        data_dir=Path(os.getenv("TOOLGATE_DATA_DIR", ROOT / "data")),
        llm_provider=os.getenv("LLM_PROVIDER", "ollama"),
        llm_model=os.getenv("LLM_MODEL", "qwen2.5:3b"),
        llm_base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        embed_provider=os.getenv("EMBED_PROVIDER", "hash"),
        embed_model=os.getenv("EMBED_MODEL", "nomic-embed-text"),
        tokens=tokens,
        max_rows=int(os.getenv("TOOLGATE_MAX_ROWS", "50")),
    )
