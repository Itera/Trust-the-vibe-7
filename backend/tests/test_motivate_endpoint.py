"""End-to-end tests for /api/motivate and /api/personas."""
from __future__ import annotations

import json

import httpx
import respx

from app.apis import advice as advice_mod
from app.apis import facts as facts_mod
from app.apis import images as images_mod
from app.apis import numbers as numbers_mod
from app.apis import quotes as quotes_mod


def _azure_reply(payload: dict) -> dict:
    return {
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": json.dumps(payload)},
            }
        ],
        "model": "gpt-4o-mini",
    }


def test_personas_endpoint(client):
    r = client.get("/api/personas")
    assert r.status_code == 200
    body = r.json()
    keys = {p["key"] for p in body}
    assert keys == {"consultant", "stoic", "nordmann", "gremlin"}
    assert all("accent_color" in p and "tagline" in p for p in body)


def test_personas_endpoint_norwegian(client):
    r = client.get("/api/personas", params={"language": "no"})
    assert r.status_code == 200
    taglines = {p["key"]: p["tagline"] for p in r.json()}
    assert "ordner seg" in taglines["nordmann"].lower()


def test_motivate_validation_requires_task(client):
    r = client.post("/api/motivate", json={"task": ""})
    assert r.status_code == 422


def test_motivate_rejects_unknown_persona(client):
    r = client.post("/api/motivate", json={"task": "hi", "persona": "wizard"})
    assert r.status_code == 422


def test_motivate_seriousness_range(client):
    r = client.post("/api/motivate", json={"task": "hi", "seriousness": 999})
    assert r.status_code == 422


@respx.mock
def test_motivate_happy_path(client, settings):
    respx.get(quotes_mod.URL).mock(
        return_value=httpx.Response(200, json={"content": "Do it.", "author": "Nike"})
    )
    respx.get(facts_mod.URL).mock(
        return_value=httpx.Response(200, json={"text": "A fact."})
    )
    respx.get(advice_mod.URL).mock(
        return_value=httpx.Response(200, json={"slip": {"advice": "Start small."}})
    )
    respx.get(numbers_mod.URL).mock(
        return_value=httpx.Response(200, json={"text": "47 is prime."})
    )
    respx.get(images_mod.URL).mock(
        return_value=httpx.Response(200, json=[{"url": "https://cat.example/a.jpg"}])
    )

    llm_payload = {
        "report_title": "Q2 DOSE",
        "report_subtitle": "For immediate consumption.",
        "cards": [
            {"kind": "peptalk", "title": "Exec Summary", "body": "You got this."},
            {"kind": "quote", "title": "Quote", "body": "Do it.", "attribution": "— Nike"},
        ],
    }
    respx.post(settings.chat_completions_url).mock(
        return_value=httpx.Response(200, json=_azure_reply(llm_payload))
    )

    r = client.post(
        "/api/motivate",
        json={
            "task": "read the news",
            "persona": "consultant",
            "language": "en",
            "seriousness": 30,
            "cards": ["peptalk", "quote"],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["task"] == "read the news"
    assert body["persona"] == "consultant"
    assert body["report_title"] == "Q2 DOSE"
    assert [c["kind"] for c in body["cards"]] == ["peptalk", "quote"]


@respx.mock
def test_motivate_upstream_llm_failure_is_502(client, settings):
    # all APIs fine; LLM dies.
    respx.get(quotes_mod.URL).mock(return_value=httpx.Response(200, json={"content": "x", "author": "y"}))
    respx.get(facts_mod.URL).mock(return_value=httpx.Response(200, json={"text": "x"}))
    respx.get(advice_mod.URL).mock(return_value=httpx.Response(200, json={"slip": {"advice": "x"}}))
    respx.get(numbers_mod.URL).mock(return_value=httpx.Response(200, json={"text": "x"}))
    respx.get(images_mod.URL).mock(return_value=httpx.Response(200, json=[{"url": "x"}]))
    respx.post(settings.chat_completions_url).mock(
        return_value=httpx.Response(401, json={"error": {"message": "bad key"}})
    )

    r = client.post("/api/motivate", json={"task": "hello"})
    assert r.status_code == 502
    assert "bad key" in r.json()["detail"]
