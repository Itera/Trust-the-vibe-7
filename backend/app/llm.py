"""Thin async client for Azure OpenAI chat completions."""
from __future__ import annotations

from typing import Any

import httpx

from .config import Settings
from .schemas import ChatMessage


class AzureOpenAIError(RuntimeError):
    """Raised when the upstream Azure OpenAI call fails."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(f"Azure OpenAI error {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


async def chat_completion(
    settings: Settings,
    messages: list[ChatMessage],
    *,
    temperature: float = 0.7,
    max_tokens: int = 512,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Call the configured Azure OpenAI deployment and return the parsed JSON."""
    payload = {
        "messages": [m.model_dump() for m in messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "api-key": settings.azure_openai_api_key,
        "Content-Type": "application/json",
    }

    async def _send(c: httpx.AsyncClient) -> httpx.Response:
        return await c.post(settings.chat_completions_url, json=payload, headers=headers)

    if client is None:
        async with httpx.AsyncClient(timeout=60.0) as c:
            resp = await _send(c)
    else:
        resp = await _send(client)

    if resp.status_code >= 400:
        # Surface a compact detail; don't leak the API key back.
        try:
            detail = resp.json()
        except ValueError:
            detail = resp.text
        raise AzureOpenAIError(resp.status_code, str(detail)[:500])

    return resp.json()
