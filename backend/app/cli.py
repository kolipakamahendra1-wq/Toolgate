"""python -m app.cli "How many deals?" --role analyst [--llm] [--json]"""
import argparse
import asyncio
import json

from .agent.graph import run_agent
from .agent.llm import get_llm
from .agent.session import stdio_session
from .services import build_services


def main() -> None:
    p = argparse.ArgumentParser(prog="toolgate")
    p.add_argument("question")
    p.add_argument("--role", default="analyst")
    p.add_argument("--llm", action="store_true", help="use the configured model (default: rule router)")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    svc = build_services()
    out = asyncio.run(run_agent(a.question, a.role, stdio_session, get_llm(svc.settings) if a.llm else None))
    if a.json:
        print(json.dumps(out, indent=2, default=str))
        return
    for step in out["trace"]:
        print(f"[{step['step']}] " + ", ".join(f"{k}={v}" for k, v in step.items() if k != "step")[:200])
    print("\n" + out["answer"])


if __name__ == "__main__":
    main()
