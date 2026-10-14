import asyncio

from app.agent.session import memory_session_factory


def test_search_respects_acl(svc):
    hr_hits = svc.vectors.search("hr_admin", "compensation bands salary")
    assert hr_hits and hr_hits[0]["doc_id"] == "hr-comp"
    analyst_hits = svc.vectors.search("analyst", "compensation bands salary")
    assert "hr-comp" not in {h["doc_id"] for h in analyst_hits}


def test_search_ranks_relevant_first(svc):
    hits = svc.vectors.search("support", "users loop on SSO login page")
    assert hits[0]["doc_id"] == "kb-sso"


def test_hash_embedding_is_stable_across_calls():
    from app.vectorstore import hash_embed
    assert (hash_embed("sso login loop") == hash_embed("sso login loop")).all()


def run_with_session(svc, role, fn):
    async def go():
        async with memory_session_factory(svc)(role) as s:
            return await fn(s)
    return asyncio.run(go())


def test_mcp_lists_tools(svc):
    tools = run_with_session(svc, "analyst", lambda s: s.tools())
    assert {t["name"] for t in tools} == {"list_tables", "run_sql", "search_docs", "get_ticket"}


def test_mcp_tool_allowed_and_audited(svc):
    res = run_with_session(svc, "analyst", lambda s: s.call("run_sql", {"sql": "SELECT COUNT(*) FROM deals"}))
    assert res.ok and res.data["rows"] == [[7]]
    assert svc.audit.recent()[0]["decision"] == "allow"


def test_mcp_tool_denied_and_audited(svc):
    res = run_with_session(svc, "analyst", lambda s: s.call("run_sql", {"sql": "SELECT salary FROM employees"}))
    assert not res.ok and res.denied
    row = svc.audit.recent()[0]
    assert row["decision"] == "deny" and row["role"] == "analyst"


def test_role_is_not_a_tool_argument(svc):
    """A caller cannot pass a role; extra args are ignored or rejected, access stays the server's role."""
    res = run_with_session(svc, "analyst", lambda s: s.call("run_sql", {"sql": "SELECT salary FROM employees", "role": "hr_admin"}))
    assert not res.ok


def test_same_question_differs_by_identity(svc):
    sql = {"sql": "SELECT name, email FROM employees WHERE id = 2"}
    hr = run_with_session(svc, "hr_admin", lambda s: s.call("run_sql", sql))
    an = run_with_session(svc, "analyst", lambda s: s.call("run_sql", sql))
    assert hr.ok and hr.data["rows"] == [["Liam Walsh", "li***"]]
    assert not an.ok and an.denied
