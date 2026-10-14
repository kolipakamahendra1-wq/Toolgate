"""`python -m app.mcp_server --role analyst` runs the MCP server over stdio for one identity."""
import argparse

from ..services import build_services
from . import build_server

p = argparse.ArgumentParser()
p.add_argument("--role", required=True)
args = p.parse_args()
build_server(args.role, build_services()).run("stdio")
