"""adviceslip.com — short unsolicited life advice."""
from __future__ import annotations

import httpx

URL = "https://api.adviceslip.com/advice"


async def fetch_advice(client: httpx.AsyncClient) -> dict[str, str]:
    """Return {'text': str}."""
    r = await client.get(URL, timeout=8.0)
    r.raise_for_status()
    data = r.json()
    slip = data.get("slip") or {}
    return {"text": str(slip.get("advice", "")).strip()}
