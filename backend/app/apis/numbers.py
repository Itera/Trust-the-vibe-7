"""numbersapi.com — trivia about random numbers."""
from __future__ import annotations

import httpx

URL = "http://numbersapi.com/random/trivia"


async def fetch_number_trivia(client: httpx.AsyncClient) -> dict[str, str]:
    """Return {'text': str}. numbersapi only speaks http, not https."""
    r = await client.get(URL, params={"json": "true"}, timeout=8.0)
    r.raise_for_status()
    data = r.json()
    return {"text": str(data.get("text", "")).strip()}
