"""Unit tests for each open-API client. Network is mocked with respx."""
from __future__ import annotations

import httpx
import pytest
import respx

from app.apis import (
    fetch_advice,
    fetch_cat_image,
    fetch_number_trivia,
    fetch_pixabay_images,
    fetch_pixabay_video,
    fetch_quote,
    fetch_useless_fact,
)
from app.apis import advice as advice_mod
from app.apis import facts as facts_mod
from app.apis import images as images_mod
from app.apis import numbers as numbers_mod
from app.apis import pixabay as pixabay_mod
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


@pytest.mark.asyncio
async def test_fetch_pixabay_images():
    body = {
        "hits": [
            {
                "webformatURL": "https://cdn.pixabay.com/photo/a_640.jpg",
                "largeImageURL": "https://cdn.pixabay.com/photo/a_1280.jpg",
                "tags": "vacation, beach",
                "pageURL": "https://pixabay.com/photos/a/",
                "user": "Author",
            },
            {
                "webformatURL": "https://cdn.pixabay.com/photo/b_640.jpg",
                "tags": "palm, sun",
                "pageURL": "https://pixabay.com/photos/b/",
                "user": "Author2",
            },
        ]
    }
    async with httpx.AsyncClient() as client:
        with respx.mock:
            route = respx.get(pixabay_mod.IMAGES_URL).mock(
                return_value=httpx.Response(200, json=body)
            )
            out = await fetch_pixabay_images(client, "k", "vacation", count=2, language="no")
    assert len(out) == 2
    assert out[0]["url"] == "https://cdn.pixabay.com/photo/a_640.jpg"
    assert out[0]["tags"] == "vacation, beach"
    # 'no' is supported by pixabay so it passes through, not falling back to en.
    assert route.calls.last.request.url.params["lang"] == "no"
    assert route.calls.last.request.url.params["safesearch"] == "true"


@pytest.mark.asyncio
async def test_fetch_pixabay_video_picks_medium_first():
    body = {
        "hits": [
            {
                "tags": "running, motivation",
                "pageURL": "https://pixabay.com/videos/x/",
                "user": "Author",
                "videos": {
                    "large": {"url": "https://cdn.pixabay.com/v/x_large.mp4", "thumbnail": "t_l.jpg"},
                    "medium": {"url": "https://cdn.pixabay.com/v/x_medium.mp4", "thumbnail": "t_m.jpg"},
                    "small": {"url": "https://cdn.pixabay.com/v/x_small.mp4", "thumbnail": "t_s.jpg"},
                    "tiny": {"url": "https://cdn.pixabay.com/v/x_tiny.mp4", "thumbnail": "t_t.jpg"},
                },
            }
        ]
    }
    async with httpx.AsyncClient() as client:
        with respx.mock:
            respx.get(pixabay_mod.VIDEOS_URL).mock(
                return_value=httpx.Response(200, json=body)
            )
            out = await fetch_pixabay_video(client, "k", "motivation")
    assert out is not None
    assert out["url"] == "https://cdn.pixabay.com/v/x_medium.mp4"
    assert out["poster"] == "t_m.jpg"


@pytest.mark.asyncio
async def test_fetch_pixabay_video_returns_none_when_empty():
    async with httpx.AsyncClient() as client:
        with respx.mock:
            respx.get(pixabay_mod.VIDEOS_URL).mock(
                return_value=httpx.Response(200, json={"hits": []})
            )
            out = await fetch_pixabay_video(client, "k", "obscure")
    assert out is None


@pytest.mark.asyncio
async def test_fetch_pixabay_falls_back_to_en_for_unknown_lang():
    async with httpx.AsyncClient() as client:
        with respx.mock:
            route = respx.get(pixabay_mod.IMAGES_URL).mock(
                return_value=httpx.Response(200, json={"hits": []})
            )
            await fetch_pixabay_images(client, "k", "q", language="xx")
    assert route.calls.last.request.url.params["lang"] == "en"
