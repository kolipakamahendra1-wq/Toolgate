"""Governance catalog: who may see which table, column and row, and how values are masked.

Policy is loaded from policy.json. Enforcement is structural: every table in a query is replaced
by a subquery that exposes only granted columns, applies the row filter and masks values. A column
the role cannot see therefore does not exist for the query, whatever the SQL says.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import sqlglot
from sqlglot import exp

POLICY_PATH = Path(__file__).with_name("policy.json")

MASKS = {
    "redact": "'***'",
    "partial": "substr({c}, 1, 2) || '***'",
}


class GovernanceError(Exception):
    """Request denied by policy or rejected by the SQL guard."""


class SqlError(GovernanceError):
    """Malformed SQL (parse or execution failure). Not a policy decision, so the agent may retry."""


@dataclass(frozen=True)
class TableGrant:
    columns: tuple[str, ...]
    row_filter: str | None
    masks: dict[str, str]


class Catalog:
    def __init__(self, data_db: Path, policy_path: Path = POLICY_PATH, max_rows: int = 50):
        self.data_db = Path(data_db)
        self.max_rows = max_rows
        raw = json.loads(Path(policy_path).read_text(encoding="utf-8"))["roles"]
        self._descriptions = {r: v["description"] for r, v in raw.items()}
        self._grants: dict[str, dict[str, TableGrant]] = {
            role: {
                table: TableGrant(tuple(g["columns"]), g.get("row_filter"), g.get("masks", {}))
                for table, g in spec["tables"].items()
            }
            for role, spec in raw.items()
        }

    # ---- introspection -------------------------------------------------
    def roles(self) -> list[str]:
        return list(self._grants)

    def describe_policy(self) -> dict:
        """Full policy, for the governance page."""
        return {
            role: {
                "description": self._descriptions[role],
                "tables": {
                    t: {"columns": list(g.columns), "row_filter": g.row_filter, "masks": g.masks}
                    for t, g in tables.items()
                },
            }
            for role, tables in self._grants.items()
        }

    def _grants_for(self, role: str) -> dict[str, TableGrant]:
        if role not in self._grants:
            raise GovernanceError(f"unknown role '{role}'")
        return self._grants[role]

    def tables(self, role: str) -> list[str]:
        return list(self._grants_for(role))

    def columns(self, role: str, table: str) -> list[str]:
        grants = self._grants_for(role)
        if table not in grants:
            raise GovernanceError(f"role '{role}' has no access to table '{table}'")
        return list(grants[table].columns)

    # ---- guarded SQL ---------------------------------------------------
    def _scoped_subquery(self, table: str, grant: TableGrant) -> str:
        cols = []
        for c in grant.columns:
            mask = grant.masks.get(c)
            cols.append(f"{MASKS[mask].format(c=c)} AS {c}" if mask else c)
        where = f" WHERE {grant.row_filter}" if grant.row_filter else ""
        return f"(SELECT {', '.join(cols)} FROM {table}{where})"

    def rewrite(self, role: str, sql: str) -> str:
        """Validate `sql` and return a version scoped to what `role` may see."""
        grants = self._grants_for(role)
        try:
            statements = sqlglot.parse(sql, read="sqlite")
        except sqlglot.errors.ParseError as e:
            raise SqlError(f"SQL parse error: {str(e)[:120]}") from e
        statements = [s for s in statements if s is not None]
        if len(statements) != 1:
            raise GovernanceError("exactly one SQL statement is allowed")
        tree = statements[0]
        if not isinstance(tree, (exp.Select, exp.Union)):
            raise GovernanceError("only SELECT statements are allowed")
        if tree.find(exp.With):
            raise GovernanceError("WITH clauses are not allowed")

        allowed_cols: set[str] = set()
        for t in list(tree.find_all(exp.Table)):
            if t.args.get("db") or t.args.get("catalog"):
                raise GovernanceError("schema-qualified tables are not allowed")
            if t.name not in grants:
                raise GovernanceError(f"role '{role}' has no access to table '{t.name}'")
            grant = grants[t.name]
            allowed_cols.update(grant.columns)
            alias = t.alias or t.name
            sub = sqlglot.parse_one(self._scoped_subquery(t.name, grant), read="sqlite")
            t.replace(exp.Subquery(this=sub.this, alias=exp.TableAlias(this=exp.to_identifier(alias))))

        aliases = {a.alias for a in tree.find_all(exp.Alias)}
        for col in tree.find_all(exp.Column):
            if col.name not in allowed_cols and col.name not in aliases:
                raise GovernanceError(f"column '{col.name}' is not available to role '{role}'")
        return tree.sql(dialect="sqlite")

    def run_select(self, role: str, sql: str) -> dict:
        scoped = self.rewrite(role, sql)
        con = sqlite3.connect(f"file:{self.data_db.as_posix()}?mode=ro", uri=True)
        try:
            con.execute("PRAGMA query_only = ON")
            cur = con.execute(scoped)
            names = [d[0] for d in cur.description]
            rows = cur.fetchmany(self.max_rows + 1)
        except sqlite3.Error as e:
            raise SqlError(f"SQL error: {e}") from e
        finally:
            con.close()
        truncated = len(rows) > self.max_rows
        return {"columns": names, "rows": [list(r) for r in rows[: self.max_rows]], "truncated": truncated}

    def get_row(self, role: str, table: str, row_id: int) -> dict:
        """Fetch one row by id through the same governed path."""
        cols = self.columns(role, table)
        res = self.run_select(role, f"SELECT {', '.join(cols)} FROM {table} WHERE id = {int(row_id)}")
        if not res["rows"]:
            raise GovernanceError(f"no visible {table} row with id {int(row_id)}")
        return dict(zip(res["columns"], res["rows"][0]))
