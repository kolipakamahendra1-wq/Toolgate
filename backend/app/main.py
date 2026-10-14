"""FastAPI front door. The bearer token decides the role; the client never states one."""
from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .agent.graph import run_agent
from .agent.llm import get_llm
from .agent.session import stdio_session
from .services import Services, build_services


class ChatIn(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    use_llm: bool = False


def create_app(svc: Services | None = None, session_cm=None) -> FastAPI:
    svc = svc or build_services()
    session_cm = session_cm or stdio_session
    app = FastAPI(title="Toolgate", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    def role_from_token(authorization: str = Header(default="")) -> str:
        token = authorization.removeprefix("Bearer ").strip()
        role = svc.settings.tokens.get(token)
        if not role:
            raise HTTPException(401, "missing or invalid bearer token")
        return role

    @app.get("/health")
    def health():
        s = svc.settings
        return {"status": "ok", "llm": s.llm_provider, "model": s.llm_model, "embeddings": s.embed_provider}

    @app.get("/api/me")
    def me(role: str = Depends(role_from_token)):
        pol = svc.catalog.describe_policy()[role]
        return {"role": role, "description": pol["description"], "tables": pol["tables"]}

    @app.get("/api/policy")
    def policy(role: str = Depends(role_from_token)):
        return {role: svc.catalog.describe_policy()[role]}  # callers see their own grants only

    @app.get("/api/audit")
    def audit(limit: int = 50, role: str = Depends(role_from_token)):
        return svc.audit.recent(max(1, min(limit, 200)), role=role)

    @app.post("/api/chat")
    async def chat(body: ChatIn, role: str = Depends(role_from_token)):
        llm = get_llm(svc.settings) if body.use_llm else None
        return await run_agent(body.question, role, session_cm, llm)

    return app


def create_default() -> FastAPI:
    """uvicorn app.main:create_default --factory --port 8030"""
    return create_app()
