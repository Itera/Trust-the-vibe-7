"""HuMotivatoren orchestrator: gather raw materials, compose persona-voiced cards."""
from __future__ import annotations

import asyncio
import json
import logging
import random
from typing import Any

import httpx

from .apis import (
    fetch_advice,
    fetch_cat_image,
    fetch_number_trivia,
    fetch_quote,
    fetch_useless_fact,
    build_meme_url,
    get_curated_templates,
)
from .config import Settings
from .guardrails import GuardrailViolation, validate_input, validate_output, validate_task_values
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
    client: httpx.AsyncClient, req: MotivationRequest
) -> dict[str, Any]:
    """Concurrently fetch everything we might want; the LLM uses what's useful."""
    wants_image = "image" in req.cards
    wants_numbers = "number_trivia" in req.cards or "kpi" in req.cards
    wants_fact = "fact" in req.cards
    wants_advice = "advice" in req.cards or "recommendation" in req.cards
    wants_quote = "quote" in req.cards

    wants_meme = "meme" in req.cards

    tasks = {
        "quote": _safe(fetch_quote(client)) if wants_quote else None,
        "fact": _safe(fetch_useless_fact(client, language=req.language)) if wants_fact else None,
        "advice": _safe(fetch_advice(client)) if wants_advice else None,
        "number_trivia": _safe(fetch_number_trivia(client)) if wants_numbers else None,
        "image": _safe(fetch_cat_image(client)) if wants_image else None,
    }

    # Meme templates are local data — no async fetch needed.
    raw_meme_templates = get_curated_templates() if wants_meme else None
    if raw_meme_templates:
        raw_meme_templates = random.sample(raw_meme_templates, len(raw_meme_templates))
    # Keep only the ones we actually requested.
    active = {k: v for k, v in tasks.items() if v is not None}
    results = await asyncio.gather(*active.values())
    out = dict(zip(active.keys(), results))
    if raw_meme_templates:
        out["meme_templates"] = raw_meme_templates
    return out


# ---------- prompt construction ---------------------------------------------

# Hard limits in plain language — no corporate framing.
VALUES_GUARDRAIL = (
    "Hard limits (every persona, no exceptions):\n"
    "- No politics, religion, or nationalism.\n"
    "- No stereotyping, body-shaming, or jokes that target any group. "
    "Humour punches sideways, never down.\n"
    "- Keep it workplace-safe and kind.\n"
    "- Don't present made-up content as real; be clear when something is fictional or satirical.\n"
    "- Celebrate effort and creativity; never mock someone's ambition.\n"
    "- If a raw material is unusable, quietly skip it."
)

# Words that make everything sound like a slide deck.
_CORPORATE_BUZZWORDS = (
    "synergy/synergies, alignment/aligned, leverage, paradigm shift, north star, "
    "low-hanging fruit, circle back, bandwidth, drill down, move the needle, "
    "scalable, value proposition, stakeholders, deliverables, action items, "
    "best practices, ROI, impact-driven, ecosystem, holistic, ideate, pivot, "
    "unlock your potential, leverage your strengths, empower, learnings, "
    "deep dive, touch base, net-net, at the end of the day, going forward"
)


def _anti_corporate_guidance(persona_key: str) -> str:
    if persona_key == "consultant":
        return (
            "LANGUAGE: Corporate jargon is your entire personality. "
            f"Weaponise these words with maximum sincerity: {_CORPORATE_BUZZWORDS}. "
            "The denser the buzzword soup, the better — that's exactly the joke."
        )
    return (
        "LANGUAGE: Absolutely zero corporate speak. Not even a little bit. "
        f"If you catch yourself reaching for any of these, stop and use a real human word instead: "
        f"{_CORPORATE_BUZZWORDS}. "
        "Write like a person talking to a friend — casual, specific, alive."
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


def _task_anchoring_guidance(task: str) -> str:
    """Return prompt instructions that force the model to mirror the user's task closely."""
    word_count = len(task.split())

    register_hint: str
    if word_count <= 4:
        register_hint = (
            "The user was terse — keep cards punchy and to-the-point, no waffle."
        )
    elif word_count <= 10:
        register_hint = (
            "Match the user's casual, conversational register throughout."
        )
    else:
        register_hint = (
            "The user gave detail — use the specifics they mentioned; go deep, not broad."
        )

    return (
        "TASK ANCHORING (critical):\n"
        "- Read the task carefully. Identify its domain, key verbs, nouns, and any "
        "jargon the user used. Weave those exact words and concepts into every card.\n"
        "- Generic motivation filler ('you've got this!', 'leverage your strengths', "
        "'unlock your potential') is FORBIDDEN unless it is ironic or in-character.\n"
        "- Each card must be so specific to this task that it would make no sense "
        "applied to a different task.\n"
        "- Echo the user's own energy: if they sound excited, match it; "
        "if they sound tired or reluctant, acknowledge it with warmth.\n"
        f"- Register note: {register_hint}"
    )


def _card_menu(kinds: list[str], language: str) -> str:
    descriptions_en = {
        "peptalk": "A 2-3 sentence hero pep talk tying everything to the user's task.",
        "quote": "A real or persona-paraphrased quote with attribution.",
        "fact": "A useless-but-charming fact, tied to the task if possible.",
        "kpi": "A fake-but-plausible consulting KPI with a trend (e.g. '+47% vibe index').",
        "advice": "One short imperative sentence of life advice.",
        "image": "A visual-aid card — use the cat image URL from raw materials.",
        "number_trivia": "A dubious stat about a specific number tied to the task.",
        "haiku": "A 5-7-5 haiku about the task.",
        "horoscope": "A 2 sentence pseudo-horoscope for today, for this task.",
        "playlist": "A 3-song fake playlist for doing this task (titles + artists, made up).",
        "testimonial": "A fake customer testimonial from 'Nils, 34' style, endorsing the task.",
        "recommendation": "A 'pair with…' recommendation (e.g. 'Pair with a 12-min timer and oat milk.').",
        "meme": (
            "A meme card. Study the 'use' field of each template in raw_materials.meme_templates "
            "and pick the ONE template whose comedic format best fits the user's task. "
            "IMPORTANT: Do NOT default to 'drake' — seriously consider ALL templates and vary your choice. "
            "At low seriousness (< 30), prefer subtle/dry templates like 'cmm', 'interesting', 'mordor', 'pooh', or 'kermit'. "
            "At medium seriousness (30-60), use versatile ones like 'astronaut', 'rollsafe', 'db', 'fry', or 'pigeon'. "
            "At high seriousness (> 60), go wild with 'fine', 'batman', 'facepalm', 'spongebob', 'panik-kalm-panik', or 'slap'. "
            "If the user's task mentions ANY person's name(s), you MUST include at least one name directly in the top_text or bottom_text — "
            "e.g. 'When Erik says it's easy' or 'Lisa watching you struggle'. This is mandatory, not optional. "
            "Set meme_template_id to the chosen id. Write a short top_text and bottom_text "
            "that are funny and directly relevant to the user's specific task. "
            "The image will be generated automatically."
        ),
    }
    descriptions_no = {
        "peptalk": "En 2-3 setningers heltemodig peptalk som binder alt til oppgaven.",
        "quote": "Et ekte eller persona-parafrasert sitat med kilde.",
        "fact": "Et unyttig men sjarmerende faktum, helst koblet til oppgaven.",
        "kpi": "En troverdig-oppdiktet konsulent-KPI med trend (f.eks. '+47 % vibbe-indeks').",
        "advice": "Én kort imperativ livsråd-setning.",
        "image": "Et visuelt kort — bruk katte-URLen fra raw materials.",
        "number_trivia": "En tvilsom statistikk om et tall knyttet til oppgaven.",
        "haiku": "Et 5-7-5 haiku om oppgaven.",
        "horoscope": "Et 2-setningers pseudo-horoskop for i dag, for denne oppgaven.",
        "playlist": "En oppdiktet 3-låts spilleliste for denne oppgaven (titler + artister).",
        "testimonial": "Et oppdiktet kundeutsagn i stil 'Nils, 34', som roser oppgaven.",
        "recommendation": "En 'kombiner med…'-anbefaling (f.eks. 'Kombiner med en 12-min timer og havremelk.').",
        "meme": (
            "Et meme-kort. Les 'use'-feltet til hver mal i raw_materials.meme_templates "
            "og velg den ENE malen som passer best til brukerens oppgave. "
            "VIKTIG: IKKE velg 'drake' som standard — vurder ALLE maler og varier valget. "
            "Ved lav seriousness (< 30), foretrekk subtile maler som 'cmm', 'interesting', 'mordor', 'pooh' eller 'kermit'. "
            "Ved middels seriousness (30-60), bruk 'astronaut', 'rollsafe', 'db', 'fry' eller 'pigeon'. "
            "Ved høy seriousness (> 60), gå vilt med 'fine', 'batman', 'facepalm', 'spongebob', 'panik-kalm-panik' eller 'slap'. "
            "Hvis brukerens oppgave nevner personnavn, MÅ du inkludere minst ett navn direkte i top_text eller bottom_text — "
            "f.eks. 'Når Erik sier det er lett' eller 'Lisa ser deg slite'. Dette er obligatorisk. "
            "Sett meme_template_id til valgt id. Skriv kort top_text og bottom_text "
            "som er morsomt og direkte relevant for brukerens spesifikke oppgave. "
            "Bildet genereres automatisk."
        ),
    }
    descs = descriptions_no if language == "no" else descriptions_en
    lines = [f"- {k}: {descs.get(k, 'Free form.')}" for k in kinds]
    return "\n".join(lines)


def build_messages(
    req: MotivationRequest,
    persona: Persona,
    raw_materials: dict[str, Any],
) -> list[dict[str, str]]:
    voice = persona.voice(req.language)
    seriousness = _seriousness_guidance(req.seriousness)
    task_anchoring = _task_anchoring_guidance(req.task)
    language_guidance = _anti_corporate_guidance(req.persona)

    language_name = "Norwegian (bokmål)" if req.language == "no" else "English"

    raw_blob = json.dumps(raw_materials, ensure_ascii=False, indent=2)

    schema_block = (
        '{\n'
        '  "report_title": "string, mock-serious report headline in persona voice",\n'
        '  "report_subtitle": "string, 1 short editorial line in persona voice",\n'
        '  "cards": [\n'
        '    {\n'
        '      "kind": "one of: " + the requested kinds,\n'
        '      "title": "short section title",\n'
        '      "body": "the card content, in persona voice",\n'
        '      "attribution": "optional — e.g. \'— Seneca\' for quotes, or null",\n'
        '      "image_url": "REQUIRED when kind == image, otherwise null",\n'
        '      "meme_template_id": "REQUIRED when kind == meme — the template id from meme_templates, otherwise null",\n'
        '      "meme_top_text": "REQUIRED when kind == meme — short top caption, otherwise null",\n'
        '      "meme_bottom_text": "REQUIRED when kind == meme — short bottom caption, otherwise null",\n'
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
        f"{language_guidance}\n\n"
        f"{task_anchoring}\n\n"
        f"{VALUES_GUARDRAIL}\n\n"
        "OUTPUT: a single JSON object matching this shape (no prose, no markdown):\n"
        f"{schema_block}\n\n"
        "Produce exactly one card per requested kind, in the requested order. "
        "Use the raw materials wherever natural — rewrite them in persona voice "
        "if it improves the piece. For the 'image' card, you MUST set image_url "
        "to the URL from raw_materials.image.url (or omit the card if missing).\n\n"
        "IMPORTANT — NAMES: If the user's task mentions any person's name(s), "
        "you MUST weave those names into the cards — especially meme captions, "
        "pep talks, testimonials, and horoscopes. Make it personal and funny."
    )

    user = (
        f"User's task: {req.task!r}\n\n"
        f"Seriousness level: {req.seriousness}/100\n\n"
        f"Requested card kinds (in order): {req.cards}\n\n"
        f"Raw materials fetched from the internet:\n{raw_blob}\n\n"
        "Before writing, briefly note to yourself (not in output): what domain is this "
        "task in, what words did the user use, what energy do they have? "
        "Then write the JSON with all of that baked in. Output only the JSON."
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
        validate_input(req.task)
        await validate_task_values(settings, req.task)
        raw = await gather_raw_materials(c, req)
        messages = build_messages(req, persona, raw)
        data = await chat_completion(
            settings,
            messages,
            temperature=0.9,
            max_tokens=1400,
            response_format={"type": "json_object"},
            client=c,
        )
        content = (
            (data.get("choices") or [{}])[0].get("message", {}).get("content", "{}")
        )
        await validate_output(settings, content)
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.warning("LLM returned invalid JSON: %s", exc)
            parsed = {"cards": []}

        cards_raw: list[dict[str, Any]] = parsed.get("cards") or []
        cards: list[Card] = []
        meme_meta: list[dict[str, Any]] = []  # parallel list for meme post-processing
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
            meme_meta.append(c_raw)

        # Ensure image cards have a URL — fall back to raw material if the model forgot.
        for card in cards:
            if card.kind == "image" and not card.image_url and raw.get("image"):
                card.image_url = raw["image"].get("url")

        # Build meme image URLs synchronously — memegen.link needs no HTTP call.
        valid_template_ids = {t["id"] for t in get_curated_templates()}
        for card, meta in zip(cards, meme_meta):
            if card.kind != "meme":
                continue
            tid = meta.get("meme_template_id")
            # Fall back to a random template if the LLM omitted or returned an unknown id.
            if not tid or tid not in valid_template_ids:
                tid = random.choice(list(valid_template_ids))
                logger.warning("LLM returned invalid/missing meme_template_id; falling back to %r", tid)
            top = meta.get("meme_top_text") or "When you need motivation"
            bot = meta.get("meme_bottom_text") or req.task
            card.image_url = build_meme_url(str(tid), top, bot)
            card.source = "memegen.link"
            logger.debug("Meme URL built: %s", card.image_url)

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
