import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.agent.session import memory_session_factory
from app.main import create_app


def client(svc):
    return TestClient(create_app(svc, memory_session_factory(svc)))


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health_is_open(svc):
    assert client(svc).get("/health").json()["status"] == "ok"


def test_chat_requires_token(svc):
    c = client(svc)
    assert c.post("/api/chat", json={"question": "hi"}).status_code == 401
    assert c.post("/api/chat", json={"question": "hi"}, headers=auth("nope")).status_code == 401


def test_token_decides_role(svc):
    c = client(svc)
    assert c.get("/api/me", headers=auth("tg-hr")).json()["role"] == "hr_admin"
    assert c.get("/api/me", headers=auth("tg-analyst")).json()["role"] == "analyst"


def test_chat_same_question_two_identities(svc):
    c = client(svc)
    q = {"question": "List all salaries"}
    hr = c.post("/api/chat", json=q, headers=auth("tg-hr")).json()
    an = c.post("/api/chat", json=q, headers=auth("tg-analyst")).json()
    assert not hr["denied"] and "182000" in hr["answer"]
    assert an["denied"] and "182000" not in an["answer"]


def test_audit_scoped_to_caller(svc):
    c = client(svc)
    c.post("/api/chat", json={"question": "List all salaries"}, headers=auth("tg-analyst"))
    c.post("/api/chat", json={"question": "headcount"}, headers=auth("tg-hr"))
    rows = c.get("/api/audit", headers=auth("tg-analyst")).json()
    assert rows and {r["role"] for r in rows} == {"analyst"}
    assert any(r["decision"] == "deny" for r in rows)


def test_policy_endpoint_hides_other_roles(svc):
    pol = client(svc).get("/api/policy", headers=auth("tg-analyst")).json()
    assert list(pol) == ["analyst"]


def test_question_validation(svc):
    assert client(svc).post("/api/chat", json={"question": ""}, headers=auth("tg-hr")).status_code == 422


def test_real_stdio_transport(tmp_path):
    """Spawns the actual MCP server process. Proves identity comes from --role and the wire protocol works."""
    root = Path(__file__).resolve().parent.parent
    env = {**os.environ, "TOOLGATE_DATA_DIR": str(tmp_path), "EMBED_PROVIDER": "hash", "LLM_PROVIDER": "none"}
    out = subprocess.run(
        [sys.executable, "-m", "app.cli", "List all salaries", "--role", "analyst"],
        cwd=root, env=env, capture_output=True, text=True, timeout=120,
    )
    assert out.returncode == 0, out.stderr[-500:]
    assert "Access denied" in out.stdout
