"""LLM clients. Ollama (free, local) by default; any OpenAI-compatible endpoint also works."""
from __future__ import annotations

from typing import Protocol

import httpx

from ..config import Settings


class LLMError(RuntimeError):
    pass


class LLM(Protocol):
    async def chat(self, messages: list[dict], json_mode: bool = False) -> str: ...


class OllamaClient:
    def __init__(self, base_url: str, model: str):
        self.base_url, self.model = base_url.rstrip("/"), model

    async def chat(self, messages: list[dict], json_mode: bool = False) -> str:
        body = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            # A 3B model at low temperature can loop on JSON output; the penalty and cap prevent a 500.
            "options": {"temperature": 0.2, "repeat_penalty": 1.15, "num_predict": 400},
        }
        if json_mode:
            body["format"] = "json"
        try:
            async with httpx.AsyncClient(timeout=600) as c:
                r = await c.post(f"{self.base_url}/api/chat", json=body)
        except httpx.HTTPError as e:
            raise LLMError(f"cannot reach Ollama at {self.base_url}: {e}") from e
        if r.status_code != 200:
            raise LLMError(f"Ollama HTTP {r.status_code}: {r.text[:300]}")
        return r.json()["message"]["content"]


class OpenAICompatClient:
    def __init__(self, base_url: str, model: str, api_key: str):
        self.base_url, self.model, self.api_key = base_url.rstrip("/"), model, api_key

    async def chat(self, messages: list[dict], json_mode: bool = False) -> str:
        body = {"model": self.model, "messages": messages, "temperature": 0.2}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        try:
            async with httpx.AsyncClient(timeout=120) as c:
                r = await c.post(f"{self.base_url}/v1/chat/completions", json=body,
                                 headers={"Authorization": f"Bearer {self.api_key}"})
        except httpx.HTTPError as e:
            raise LLMError(f"cannot reach {self.base_url}: {e}") from e
        if r.status_code != 200:
            raise LLMError(f"HTTP {r.status_code}: {r.text[:300]}")
        return r.json()["choices"][0]["message"]["content"]


def get_llm(s: Settings) -> LLM | None:
    """None means 'no model': the agent uses its deterministic router and template answers."""
    if s.llm_provider == "ollama":
        return OllamaClient(s.llm_base_url, s.llm_model)
    if s.llm_provider == "openai":
        return OpenAICompatClient(s.llm_base_url, s.llm_model, s.llm_api_key)
    return None
