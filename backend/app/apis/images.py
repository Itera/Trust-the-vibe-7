"""thecatapi.com — one cat per request, no key required for single-image search."""
from __future__ import annotations

import httpx

URL = "https://api.thecatapi.com/v1/images/search"


async def fetch_cat_image(client: httpx.AsyncClient) -> dict[str, str]:
    """Return {'url': str}."""
    r = await client.get(URL, timeout=8.0)
    r.raise_for_status()
    items = r.json()
    first = items[0] if isinstance(items, list) and items else {}
    return {"url": str(first.get("url", "")).strip()}
