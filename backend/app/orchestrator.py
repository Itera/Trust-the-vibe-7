"""HuMotivatoren orchestrator: gather raw materials, compose persona-voiced cards."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

from .apis import (
    fetch_advice,
    fetch_cat_image,
    fetch_number_trivia,
    fetch_pixabay_images,
    fetch_pixabay_video,
    fetch_quote,
    fetch_useless_fact,
)
from .config import Settings
from .llm import chat_completion
from .personas import Persona, get_persona
from .schemas import Card, MotivationPackage, MotivationRequest

logger = logging.getLogger("humotivatoren")


# ---------- raw material gathering ------------------------------------------

async def _safe(coro) -> Any:
    try:
        return await coro
    except Exception as exc:  # any network / parse failure — just skip that source
        logger.info("raw material fetch failed: %s", exc)
        return None


async def gather_raw_materials(
    client: httpx.AsyncClient,
    settings: Settings,
    req: MotivationRequest,
) -> dict[str, Any]:
    """Concurrently fetch everything we might want; the LLM uses what's useful."""
    wants_image = "image" in req.cards
    wants_numbers = "number_trivia" in req.cards or "kpi" in req.cards
    wants_fact = "fact" in req.cards
    wants_advice = "advice" in req.cards or "recommendation" in req.cards
    wants_quote = "quote" in req.cards
    wants_video = "video" in req.cards
    wants_mood = "mood_board" in req.cards

    pixabay_key = settings.pixabay_api_key
    # A simple keyword-ish query derived from the user's task.
    pix_query = req.task[:80]

    tasks: dict[str, Any] = {
        "quote": _safe(fetch_quote(client)) if wants_quote else None,
        "fact": _safe(fetch_useless_fact(client, language=req.language)) if wants_fact else None,
        "advice": _safe(fetch_advice(client)) if wants_advice else None,
        "number_trivia": _safe(fetch_number_trivia(client)) if wants_numbers else None,
        "image": _safe(fetch_cat_image(client)) if wants_image else None,
    }
    if pixabay_key and wants_video:
        tasks["video"] = _safe(
            fetch_pixabay_video(client, pixabay_key, pix_query, language=req.language)
        )
    if pixabay_key and wants_mood:
        tasks["mood_board"] = _safe(
            fetch_pixabay_images(
                client, pixabay_key, pix_query, count=4, language=req.language
            )
        )

    active = {k: v for k, v in tasks.items() if v is not None}
    results = await asyncio.gather(*active.values())
    return dict(zip(active.keys(), results))


# ---------- prompt construction ---------------------------------------------

VALUES_GUARDRAIL = (
    "Absolute rules: keep it warm, cheeky, absurd-but-kind. Never mean-spirited. "
    "No politics, religion, nationalism, body-shaming, or stereotyping. "
    "Stay workplace-safe. Humor punches sideways, never down. "
    "If a source is unusable, quietly skip it."
)


def _seriousness_guidance(level: int) -> str:
    if level < 20:
        return "Tone: fully deadpan professional, like a real consulting deliverable."
    if level < 45:
        return "Tone: mostly professional with a subtle absurd undercurrent."
    if level < 70:
        return "Tone: balanced — professional structure, openly playful content."
    if level < 90:
        return "Tone: leaning unhinged; corporate shell with chaotic filling."
    return "Tone: maximum unhinged energy while staying kind and on-brand."


def build_messages(
    req: MotivationRequest,
    persona: Persona,
    raw_materials: dict[str, Any],
) -> list[dict[str, str]]:
    voice = persona.voice(req.language)
    seriousness = _seriousness_guidance(req.seriousness)

    language_name = "Norwegian (bokmål)" if req.language == "no" else "English"

    raw_blob = json.dumps(raw_materials, ensure_ascii=False, indent=2)

    schema_block = (
        '{\n'
        '  "report_title": "string, mock-serious report headline in persona voice",\n'
        '  "report_subtitle": "string, 1 short editorial line in persona voice",\n'
        '  "cards": [\n'
        '    {\n'
        '      "kind": "one of the requested kinds",\n'
        '      "title": "short section title",\n'
        '      "body": "the card content, in persona voice",\n'
        '      "attribution": "optional — e.g. \'— Seneca\' for quotes, or null",\n'
        '      "image_url": "REQUIRED when kind == image, otherwise null",\n'
        '      "source": "optional — e.g. \'quotable.io\' or \'HuMotivatoren\'"\n'
        '    }\n'
        '  ]\n'
        '}'
    )

    system = (
        "You are the HuMotivatoren orchestrator, composing a satirical-but-warm "
        "motivation deck for a colleague at Itera.\n\n"
        f"PERSONA: {persona.name}\n"
        f"VOICE INSTRUCTIONS: {voice}\n"
        f"RESPONSE LANGUAGE: {language_name}. Write ALL user-facing text in this language.\n"
        f"{seriousness}\n\n"
        f"{VALUES_GUARDRAIL}\n\n"
        "OUTPUT: a single JSON object matching this shape (no prose, no markdown):\n"
        f"{schema_block}\n\n"
        "Produce at most one card per requested kind, in the requested order. "
        "Use the raw materials wherever natural — rewrite them in persona voice "
        "if it improves the piece.\n"
        "- For 'image' cards, you MUST set image_url to raw_materials.image.url.\n"
        "- For 'video' cards, the MP4 is injected from raw_materials.video; just "
        "write a persona-voiced title + body captioning what's coming. Skip the "
        "video card if raw_materials.video is missing.\n"
        "- For 'mood_board' cards, four image URLs are injected from "
        "raw_materials.mood_board; write a persona-voiced title + body that "
        "frames the collage. Skip if raw_materials.mood_board is empty."
    )

    user = (
        f"User's task: {req.task!r}\n\n"
        f"Requested card kinds (in order): {req.cards}\n\n"
        f"Raw materials fetched from the internet:\n{raw_blob}\n\n"
        "Now produce the JSON."
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


# ---------- main entrypoint --------------------------------------------------

async def motivate(
    settings: Settings,
    req: MotivationRequest,
    *,
    client: httpx.AsyncClient | None = None,
) -> MotivationPackage:
    persona = get_persona(req.persona)

    async def _do(c: httpx.AsyncClient) -> MotivationPackage:
        raw = await gather_raw_materials(c, settings, req)
        messages = build_messages(req, persona, raw)
        data = await chat_completion(
            settings,
            messages,
            temperature=0.9,
            max_tokens=1600,
            response_format={"type": "json_object"},
            client=c,
        )
        content = (
            (data.get("choices") or [{}])[0].get("message", {}).get("content", "{}")
        )
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.warning("LLM returned invalid JSON: %s", exc)
            parsed = {"cards": []}

        cards_raw: list[dict[str, Any]] = parsed.get("cards") or []
        cards: list[Card] = []
        allowed = set(req.cards)
        for c_raw in cards_raw:
            kind = c_raw.get("kind")
            if kind not in allowed:
                continue
            title = (c_raw.get("title") or "").strip() or kind.title()
            body = (c_raw.get("body") or "").strip()
            cards.append(
                Card(
                    kind=kind,  # type: ignore[arg-type]
                    title=title,
                    body=body,
                    attribution=(c_raw.get("attribution") or None),
                    image_url=(c_raw.get("image_url") or None),
                    source=(c_raw.get("source") or None),
                )
            )

        # Inject media URLs from raw materials (LLM only produces captions).
        cards = _inject_media_urls(cards, raw)
        # Drop cards whose required media is missing.
        cards = [c for c in cards if not _card_is_broken(c)]

        return MotivationPackage(
            task=req.task,
            persona=req.persona,
            language=req.language,
            report_title=str(parsed.get("report_title", "MOTIVATION DOSE")).strip(),
            report_subtitle=str(parsed.get("report_subtitle", "")).strip(),
            cards=cards,
        )

    if client is None:
        # LLM calls can take 10-30s; open APIs are bounded individually.
        async with httpx.AsyncClient(timeout=60.0) as c:
            return await _do(c)
    return await _do(client)


def _inject_media_urls(cards: list[Card], raw: dict[str, Any]) -> list[Card]:
    """Overwrite LLM-reported URLs with the real ones from raw_materials."""
    for card in cards:
        if card.kind == "image":
            if not card.image_url and raw.get("image"):
                card.image_url = (raw["image"] or {}).get("url")
        elif card.kind == "video" and raw.get("video"):
            video = raw["video"] or {}
            card.video_url = video.get("url")
            card.video_poster = video.get("poster")
            card.source = card.source or "pixabay.com"
        elif card.kind == "mood_board" and raw.get("mood_board"):
            urls = [item.get("url") for item in (raw["mood_board"] or []) if item.get("url")]
            card.image_urls = urls[:4] or None
            card.source = card.source or "pixabay.com"
    return cards


def _card_is_broken(card: Card) -> bool:
    """True if a media-bearing card ended up without the URL it needs."""
    if card.kind == "video":
        return not card.video_url
    if card.kind == "mood_board":
        return not card.image_urls
    return False
