"""Wires catalog, vector index and audit log from settings; builds seed data on first use."""
from __future__ import annotations

from dataclasses import dataclass

from .audit import AuditLog
from .catalog import Catalog
from .config import Settings, get_settings
from .seed import DOCS, build_data_db
from .vectorstore import VectorStore


@dataclass
class Services:
    catalog: Catalog
    vectors: VectorStore
    audit: AuditLog
    settings: Settings


def build_services(settings: Settings | None = None, rebuild: bool = False) -> Services:
    s = settings or get_settings()
    data_db = s.data_dir / "data.db"
    vectors = VectorStore(s.data_dir / "vectors.db", s.embed_provider, s.llm_base_url, s.embed_model)
    if rebuild or not data_db.exists():
        build_data_db(data_db)
        vectors.index(DOCS)
    return Services(
        catalog=Catalog(data_db, max_rows=s.max_rows),
        vectors=vectors,
        audit=AuditLog(s.data_dir / "audit.db"),
        settings=s,
    )
