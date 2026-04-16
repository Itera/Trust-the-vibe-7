"""Tests for the /api/chat endpoint. The upstream Azure call is mocked via respx."""
from __future__ import annotations

import httpx
import respx


def _azure_reply(content: str = "Hello, world!") -> dict:
    return {
        "id": "chatcmpl-xyz",
        "object": "chat.completion",
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": content},
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
    }


@respx.mock
def test_chat_happy_path(client, settings):
    route = respx.post(settings.chat_completions_url).mock(
        return_value=httpx.Response(200, json=_azure_reply("hi there!"))
    )

    r = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "hey"}]},
    )

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reply"] == "hi there!"
    assert body["model"] == "gpt-4o-mini"
    assert body["usage"]["total_tokens"] == 14

    # The upstream call actually went out with the right payload + header.
    import json as _json

    assert route.called
    sent = route.calls.last.request
    assert sent.headers["api-key"] == settings.azure_openai_api_key
    body_sent = _json.loads(sent.content)
    assert body_sent["messages"] == [{"role": "user", "content": "hey"}]
    assert body_sent["temperature"] == 0.7
    assert body_sent["max_tokens"] == 512


def test_chat_rejects_empty_messages(client):
    r = client.post("/api/chat", json={"messages": []})
    assert r.status_code == 422


def test_chat_rejects_bad_role(client):
    r = client.post(
        "/api/chat",
        json={"messages": [{"role": "pirate", "content": "arr"}]},
    )
    assert r.status_code == 422


@respx.mock
def test_chat_upstream_error_is_502(client, settings):
    respx.post(settings.chat_completions_url).mock(
        return_value=httpx.Response(401, json={"error": {"message": "bad key"}})
    )

    r = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "hey"}]},
    )
    assert r.status_code == 502
    assert "bad key" in r.json()["detail"]


@respx.mock
def test_chat_empty_choices_is_502(client, settings):
    respx.post(settings.chat_completions_url).mock(
        return_value=httpx.Response(200, json={"choices": []})
    )

    r = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "hey"}]},
    )
    assert r.status_code == 502
    assert r.json()["detail"] == "empty response from model"
