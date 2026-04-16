"""Unit tests for each open-API client. Network is mocked with respx."""
from __future__ import annotations

import httpx
import pytest
import respx

from app.apis import (
    fetch_advice,
    fetch_cat_image,
    fetch_number_trivia,
    fetch_quote,
    fetch_useless_fact,
)
from app.apis import advice as advice_mod
from app.apis import facts as facts_mod
from app.apis import images as images_mod
from app.apis import numbers as numbers_mod
from app.apis import quotes as quotes_mod


@pytest.mark.asyncio
async def test_fetch_quote():
    async with httpx.AsyncClient() as client:
        with respx.mock:
            respx.get(quotes_mod.URL).mock(
                return_value=httpx.Response(
                    200, json={"content": "Keep going.", "author": "Marcus"}
                )
            )
            out = await fetch_quote(client)
    assert out == {"text": "Keep going.", "author": "Marcus"}


@pytest.mark.asyncio
async def test_fetch_useless_fact_language_fallback():
    async with httpx.AsyncClient() as client:
        with respx.mock:
            route = respx.get(facts_mod.URL).mock(
                return_value=httpx.Response(200, json={"text": "a useless fact"})
            )
            out = await fetch_useless_fact(client, language="no")
    assert out == {"text": "a useless fact"}
    # Norwegian falls back to en at the API level.
    assert route.calls.last.request.url.params["language"] == "en"


@pytest.mark.asyncio
async def test_fetch_advice():
    async with httpx.AsyncClient() as client:
        with respx.mock:
            respx.get(advice_mod.URL).mock(
                return_value=httpx.Response(200, json={"slip": {"advice": "Drink water."}})
            )
            out = await fetch_advice(client)
    assert out == {"text": "Drink water."}


@pytest.mark.asyncio
async def test_fetch_number_trivia():
    async with httpx.AsyncClient() as client:
        with respx.mock:
            respx.get(numbers_mod.URL).mock(
                return_value=httpx.Response(200, json={"text": "47 is a prime number."})
            )
            out = await fetch_number_trivia(client)
    assert out == {"text": "47 is a prime number."}


@pytest.mark.asyncio
async def test_fetch_cat_image():
    async with httpx.AsyncClient() as client:
        with respx.mock:
            respx.get(images_mod.URL).mock(
                return_value=httpx.Response(200, json=[{"url": "https://cat.example/kitty.jpg"}])
            )
            out = await fetch_cat_image(client)
    assert out == {"url": "https://cat.example/kitty.jpg"}


@pytest.mark.asyncio
async def test_api_raises_on_5xx():
    async with httpx.AsyncClient() as client:
        with respx.mock:
            respx.get(quotes_mod.URL).mock(return_value=httpx.Response(500))
            with pytest.raises(httpx.HTTPStatusError):
                await fetch_quote(client)
