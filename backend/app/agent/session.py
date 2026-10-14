"""Opens an MCP client session bound to one role.

`stdio` spawns the real server process with --role (production path).
`memory` connects in-process (tests). Both speak the same MCP protocol.
"""
from __future__ import annotations

import json
import os
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.memory import create_connected_server_and_client_session

from ..config import ROOT
from ..mcp_server import build_server
from ..services import Services


@dataclass
class ToolResult:
    ok: bool
    denied: bool
    data: object  # parsed JSON on success, error text on failure


class ToolSession:
    def __init__(self, session: ClientSession):
        self._s = session

    async def tools(self) -> list[dict]:
        res = await self._s.list_tools()
        return [{"name": t.name, "description": t.description or "", "schema": t.inputSchema} for t in res.tools]

    async def call(self, name: str, args: dict) -> ToolResult:
        res = await self._s.call_tool(name, args)
        text = "".join(getattr(c, "text", "") for c in res.content)
        if res.isError:
            return ToolResult(False, "DENIED:" in text, text)
        structured = getattr(res, "structuredContent", None)
        if structured is not None:  # FastMCP wraps non-object returns as {"result": ...}
            return ToolResult(True, False, structured["result"] if set(structured) == {"result"} else structured)
        try:
            return ToolResult(True, False, json.loads(text))
        except json.JSONDecodeError:
            return ToolResult(True, False, text)


@asynccontextmanager
async def stdio_session(role: str):
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "app.mcp_server", "--role", role],
        cwd=str(ROOT), env=dict(os.environ),  # the SDK passes a minimal env by default; settings live in env
    )
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            yield ToolSession(s)


def memory_session_factory(svc: Services):
    @asynccontextmanager
    async def memory_session(role: str):
        server = build_server(role, svc)
        async with create_connected_server_and_client_session(server._mcp_server) as s:
            yield ToolSession(s)

    return memory_session
