"""Append-only audit log of every governed tool call, allowed or denied."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path


class AuditLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.execute(
                "CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, "
                "role TEXT, tool TEXT, args TEXT, decision TEXT, detail TEXT)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=10)

    def record(self, role: str, tool: str, args: dict, decision: str, detail: str = "") -> None:
        with self._connect() as con:
            con.execute(
                "INSERT INTO audit (ts, role, tool, args, decision, detail) VALUES (?,?,?,?,?,?)",
                (time.time(), role, tool, json.dumps(args, default=str)[:500], decision, detail[:300]),
            )

    def recent(self, limit: int = 50, role: str | None = None) -> list[dict]:
        q = "SELECT id, ts, role, tool, args, decision, detail FROM audit"
        params: list = []
        if role:
            q += " WHERE role = ?"
            params.append(role)
        q += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self._connect() as con:
            rows = con.execute(q, params).fetchall()
        keys = ("id", "ts", "role", "tool", "args", "decision", "detail")
        return [dict(zip(keys, r)) for r in rows]
