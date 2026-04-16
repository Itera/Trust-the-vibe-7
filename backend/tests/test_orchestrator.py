"""Tests for the motivate orchestrator — APIs + LLM are mocked."""
from __future__ import annotations

import json

import httpx
import pytest
import respx

from app.apis import advice as advice_mod
from app.apis import facts as facts_mod
from app.apis import images as images_mod
from app.apis import numbers as numbers_mod
from app.apis import quotes as quotes_mod
from app.orchestrator import motivate
from app.schemas import MotivationRequest


def _azure_reply(payload: dict) -> dict:
    return {
        "id": "chatcmpl-x",
        "object": "chat.completion",
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": json.dumps(payload)},
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
    }


@respx.mock
@pytest.mark.asyncio
async def test_motivate_happy_path(settings):
    respx.get(quotes_mod.URL).mock(
        return_value=httpx.Response(200, json={"content": "Do it.", "author": "Nike"})
    )
    respx.get(facts_mod.URL).mock(
        return_value=httpx.Response(200, json={"text": "Cats sleep 70% of their lives."})
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
        "report_title": "Q2 MOTIVATION DOSE",
        "report_subtitle": "Aligning vibes with strategic intent.",
        "cards": [
            {"kind": "peptalk", "title": "Executive Summary", "body": "You got this."},
            {"kind": "quote", "title": "Quote", "body": "Do it.", "attribution": "— Nike"},
            {"kind": "fact", "title": "Did you know", "body": "Cats sleep."},
            {"kind": "kpi", "title": "KPI", "body": "+47% vibe index"},
            {"kind": "advice", "title": "Advice", "body": "Start small."},
            {"kind": "image", "title": "Visual", "body": "Behold.", "image_url": "https://cat.example/a.jpg"},
            {"kind": "haiku", "title": "Haiku", "body": "Five then seven then / five again and fin."},
            {"kind": "recommendation", "title": "Pair with", "body": "Coffee"},
        ],
    }
    respx.post(settings.chat_completions_url).mock(
        return_value=httpx.Response(200, json=_azure_reply(llm_payload))
    )

    req = MotivationRequest(
        task="read the news", persona="consultant", language="en", seriousness=30
    )
    pkg = await motivate(settings, req)

    assert pkg.task == "read the news"
    assert pkg.persona == "consultant"
    assert pkg.report_title == "Q2 MOTIVATION DOSE"
    assert {c.kind for c in pkg.cards} >= {"peptalk", "quote", "fact", "kpi", "advice", "image"}
    image_card = next(c for c in pkg.cards if c.kind == "image")
    assert image_card.image_url == "https://cat.example/a.jpg"


@respx.mock
@pytest.mark.asyncio
async def test_motivate_falls_back_image_url_when_llm_forgets(settings):
    respx.get(quotes_mod.URL).mock(return_value=httpx.Response(200, json={"content": "x", "author": "y"}))
    respx.get(facts_mod.URL).mock(return_value=httpx.Response(200, json={"text": "x"}))
    respx.get(advice_mod.URL).mock(return_value=httpx.Response(200, json={"slip": {"advice": "x"}}))
    respx.get(numbers_mod.URL).mock(return_value=httpx.Response(200, json={"text": "x"}))
    respx.get(images_mod.URL).mock(
        return_value=httpx.Response(200, json=[{"url": "https://cat.example/fallback.jpg"}])
    )

    # LLM returns an image card but forgets image_url
    llm_payload = {
        "report_title": "x",
        "report_subtitle": "y",
        "cards": [
            {"kind": "peptalk", "title": "p", "body": "b"},
            {"kind": "image", "title": "v", "body": "v"},
        ],
    }
    respx.post(settings.chat_completions_url).mock(
        return_value=httpx.Response(200, json=_azure_reply(llm_payload))
    )

    req = MotivationRequest(task="x", cards=["peptalk", "image"])
    pkg = await motivate(settings, req)
    image_card = next(c for c in pkg.cards if c.kind == "image")
    assert image_card.image_url == "https://cat.example/fallback.jpg"


@respx.mock
@pytest.mark.asyncio
async def test_motivate_skips_unknown_card_kinds(settings):
    respx.get(quotes_mod.URL).mock(return_value=httpx.Response(200, json={"content": "x", "author": "y"}))
    respx.post(settings.chat_completions_url).mock(
        return_value=httpx.Response(
            200,
            json=_azure_reply(
                {
                    "report_title": "t",
                    "report_subtitle": "s",
                    "cards": [
                        {"kind": "peptalk", "title": "p", "body": "b"},
                        {"kind": "forbidden_kind", "title": "nope", "body": "no"},
                        {"kind": "quote", "title": "q", "body": "q", "attribution": "— a"},
                    ],
                }
            ),
        )
    )

    req = MotivationRequest(task="x", cards=["peptalk", "quote"])
    pkg = await motivate(settings, req)
    kinds = [c.kind for c in pkg.cards]
    assert kinds == ["peptalk", "quote"]


@respx.mock
@pytest.mark.asyncio
async def test_motivate_tolerates_source_failure(settings):
    # quotes 500s, but everything else continues.
    respx.get(quotes_mod.URL).mock(return_value=httpx.Response(500))
    respx.get(facts_mod.URL).mock(return_value=httpx.Response(200, json={"text": "x"}))
    respx.get(advice_mod.URL).mock(return_value=httpx.Response(200, json={"slip": {"advice": "x"}}))
    respx.get(numbers_mod.URL).mock(return_value=httpx.Response(200, json={"text": "x"}))
    respx.get(images_mod.URL).mock(return_value=httpx.Response(200, json=[{"url": "https://cat.example/a.jpg"}]))
    respx.post(settings.chat_completions_url).mock(
        return_value=httpx.Response(
            200,
            json=_azure_reply(
                {
                    "report_title": "t",
                    "report_subtitle": "s",
                    "cards": [{"kind": "peptalk", "title": "p", "body": "b"}],
                }
            ),
        )
    )

    req = MotivationRequest(task="x")
    pkg = await motivate(settings, req)
    assert pkg.cards[0].kind == "peptalk"


@respx.mock
@pytest.mark.asyncio
async def test_motivate_handles_malformed_llm_json(settings):
    respx.get(quotes_mod.URL).mock(return_value=httpx.Response(200, json={"content": "x", "author": "y"}))
    respx.get(facts_mod.URL).mock(return_value=httpx.Response(200, json={"text": "x"}))
    respx.get(advice_mod.URL).mock(return_value=httpx.Response(200, json={"slip": {"advice": "x"}}))
    respx.get(numbers_mod.URL).mock(return_value=httpx.Response(200, json={"text": "x"}))
    respx.get(images_mod.URL).mock(return_value=httpx.Response(200, json=[{"url": "https://cat.example/a.jpg"}]))

    # LLM returns not-JSON content.
    respx.post(settings.chat_completions_url).mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "this is not json"},
                    }
                ],
                "model": "gpt-4o-mini",
            },
        )
    )

    req = MotivationRequest(task="x")
    pkg = await motivate(settings, req)
    assert pkg.cards == []
    assert pkg.task == "x"
