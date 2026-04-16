"""uselessfacts.jsph.pl — random facts of dubious utility."""
from __future__ import annotations

import httpx

URL = "https://uselessfacts.jsph.pl/api/v2/facts/random"


async def fetch_useless_fact(
    client: httpx.AsyncClient, *, language: str = "en"
) -> dict[str, str]:
    """Return {'text': str}. API only supports en/de — fall back to en otherwise."""
    lang = "en" if language not in {"en", "de"} else language
    r = await client.get(URL, params={"language": lang}, timeout=8.0)
    r.raise_for_status()
    data = r.json()
    return {"text": str(data.get("text", "")).strip()}
