"""Small vector index in SQLite with per-document role ACLs.

Embedders: `hash` (feature hashing, no model, deterministic) and `ollama` (nomic-embed-text).
The ACL filter runs before ranking, so a document a role may not read never enters its results.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import httpx
import numpy as np

DIM = 256
_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {"the", "a", "an", "of", "to", "and", "or", "in", "on", "for", "is", "are", "if", "it", "with", "by", "be", "as"}


def _stable_hash(tok: str) -> int:
    """FNV-1a. Python's hash() changes per process, which would break a persisted index."""
    h = 2166136261
    for ch in tok.encode():
        h = ((h ^ ch) * 16777619) & 0xFFFFFFFF
    return h


def hash_embed(text: str) -> np.ndarray:
    v = np.zeros(DIM, dtype=np.float32)
    for tok in _TOKEN.findall(text.lower()):
        if tok not in _STOP:
            v[_stable_hash(tok) % DIM] += 1.0
    n = np.linalg.norm(v)
    return v / n if n else v


def ollama_embed(text: str, base_url: str, model: str) -> np.ndarray:
    r = httpx.post(f"{base_url}/api/embeddings", json={"model": model, "prompt": text}, timeout=60)
    r.raise_for_status()
    v = np.array(r.json()["embedding"], dtype=np.float32)
    n = np.linalg.norm(v)
    return v / n if n else v


class VectorStore:
    def __init__(self, path: Path, provider: str = "hash", base_url: str = "", model: str = ""):
        self.path = Path(path)
        self.provider, self.base_url, self.model = provider, base_url, model
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as con:
            con.execute(
                "CREATE TABLE IF NOT EXISTS docs (doc_id TEXT PRIMARY KEY, title TEXT, text TEXT, "
                "roles TEXT, vec BLOB)"
            )

    def _embed(self, text: str) -> np.ndarray:
        if self.provider == "ollama":
            return ollama_embed(text, self.base_url, self.model)
        return hash_embed(text)

    def index(self, docs: list[tuple[str, str, list[str], str]]) -> None:
        with sqlite3.connect(self.path) as con:
            con.execute("DELETE FROM docs")
            for doc_id, title, roles, text in docs:
                vec = self._embed(f"{title}. {text}")
                con.execute(
                    "INSERT INTO docs VALUES (?,?,?,?,?)",
                    (doc_id, title, text, json.dumps(roles), vec.astype(np.float32).tobytes()),
                )

    def search(self, role: str, query: str, k: int = 3) -> list[dict]:
        q = self._embed(query)
        with sqlite3.connect(self.path) as con:
            rows = con.execute("SELECT doc_id, title, text, roles, vec FROM docs").fetchall()
        hits = []
        for doc_id, title, text, roles, blob in rows:
            if role not in json.loads(roles):
                continue
            score = float(np.dot(q, np.frombuffer(blob, dtype=np.float32)))
            hits.append({"doc_id": doc_id, "title": title, "text": text, "score": round(score, 4)})
        hits.sort(key=lambda h: h["score"], reverse=True)
        return [h for h in hits[:k] if h["score"] > 0]
