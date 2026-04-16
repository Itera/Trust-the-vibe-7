"""Pixabay — one key, keyword-searchable images + videos.

Docs: https://pixabay.com/api/docs/
"""
from __future__ import annotations

import httpx

IMAGES_URL = "https://pixabay.com/api/"
VIDEOS_URL = "https://pixabay.com/api/videos/"

# Pixabay's language param supports a subset; map unknowns to 'en'.
_SUPPORTED_LANGS = {
    "cs", "da", "de", "en", "es", "fr", "id", "it", "hu", "nl",
    "no", "pl", "pt", "ro", "sk", "fi", "sv", "tr", "vi", "th",
    "bg", "ru", "el", "ja", "ko", "zh",
}


def _lang(code: str) -> str:
    return code if code in _SUPPORTED_LANGS else "en"


async def fetch_images(
    client: httpx.AsyncClient,
    api_key: str,
    query: str,
    *,
    count: int = 4,
    language: str = "en",
) -> list[dict[str, str]]:
    """Return up to `count` image hits as [{url, tags, page_url, user}, ...]."""
    params = {
        "key": api_key,
        "q": query,
        "image_type": "photo",
        "orientation": "horizontal",
        "safesearch": "true",
        "per_page": max(3, min(count * 2, 20)),  # API requires per_page >= 3
        "lang": _lang(language),
    }
    r = await client.get(IMAGES_URL, params=params, timeout=10.0)
    r.raise_for_status()
    data = r.json()
    hits = data.get("hits") or []
    return [
        {
            "url": h.get("webformatURL") or h.get("largeImageURL") or "",
            "tags": h.get("tags") or "",
            "page_url": h.get("pageURL") or "",
            "user": h.get("user") or "",
        }
        for h in hits[:count]
    ]


async def fetch_video(
    client: httpx.AsyncClient,
    api_key: str,
    query: str,
    *,
    language: str = "en",
) -> dict[str, str] | None:
    """Return {url, poster, tags, page_url, user} for one video, or None."""
    params = {
        "key": api_key,
        "q": query,
        "safesearch": "true",
        "per_page": 3,
        "lang": _lang(language),
    }
    r = await client.get(VIDEOS_URL, params=params, timeout=10.0)
    r.raise_for_status()
    data = r.json()
    hits = data.get("hits") or []
    if not hits:
        return None

    first = hits[0]
    videos = first.get("videos") or {}
    # Prefer 'medium' (720p) for performance, fall back to anything available.
    for size in ("medium", "small", "large", "tiny"):
        v = videos.get(size)
        if v and v.get("url"):
            return {
                "url": v.get("url", ""),
                "poster": v.get("thumbnail", ""),
                "tags": first.get("tags") or "",
                "page_url": first.get("pageURL") or "",
                "user": first.get("user") or "",
            }
    return None
