"""quotable.io — short philosophical / inspirational quotes."""
from __future__ import annotations

import httpx

URL = "https://api.quotable.io/random"


async def fetch_quote(
    client: httpx.AsyncClient, *, max_length: int = 160
) -> dict[str, str]:
    """Return {'text': str, 'author': str}. Raises on non-2xx."""
    r = await client.get(URL, params={"maxLength": max_length}, timeout=8.0)
    r.raise_for_status()
    data = r.json()
    return {
        "text": str(data.get("content", "")).strip(),
        "author": str(data.get("author", "Unknown")).strip(),
    }
