"""MCP server. Identity is fixed when the server is built, never taken from tool arguments."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..catalog import GovernanceError, SqlError
from ..services import Services


def build_server(role: str, svc: Services) -> FastMCP:
    if role not in svc.catalog.roles():
        raise ValueError(f"unknown role '{role}'")
    mcp = FastMCP(f"toolgate-{role}")

    def governed(tool: str, args: dict, fn):
        """Run `fn`, audit the outcome, convert policy failures into MCP tool errors."""
        try:
            out = fn()
        except SqlError as e:  # must precede GovernanceError: it is a subclass
            svc.audit.record(role, tool, args, "error", str(e))
            raise ValueError(f"ERROR: {e}") from e
        except GovernanceError as e:
            svc.audit.record(role, tool, args, "deny", str(e))
            raise ValueError(f"DENIED: {e}") from e
        size = len(out["rows"]) if isinstance(out, dict) and "rows" in out else ""
        svc.audit.record(role, tool, args, "allow", f"rows={size}" if size != "" else "")
        return out

    @mcp.tool()
    def list_tables() -> list[dict]:
        """List the tables this identity may query, with the columns it may see."""
        return governed("list_tables", {}, lambda: [
            {"table": t, "columns": svc.catalog.columns(role, t)} for t in svc.catalog.tables(role)
        ])

    @mcp.tool()
    def run_sql(sql: str) -> dict:
        """Run one read-only SQL SELECT (SQLite dialect) over the tables from list_tables."""
        return governed("run_sql", {"sql": sql}, lambda: svc.catalog.run_select(role, sql))

    @mcp.tool()
    def search_docs(query: str, k: int = 3) -> list[dict]:
        """Semantic search over the knowledge base. Only documents this identity may read are searched."""
        return governed("search_docs", {"query": query, "k": k},
                        lambda: svc.vectors.search(role, query, max(1, min(k, 5))))

    @mcp.tool()
    def get_ticket(ticket_id: int) -> dict:
        """Fetch one support ticket by id."""
        return governed("get_ticket", {"ticket_id": ticket_id},
                        lambda: svc.catalog.get_row(role, "tickets", ticket_id))

    return mcp
