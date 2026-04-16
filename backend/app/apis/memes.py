"""memegen.link — free, no-auth meme generation.

API docs: https://api.memegen.link/docs
Image URL pattern: https://api.memegen.link/images/{template_id}/{top}/{bottom}.png
No credentials required — the URL itself IS the generated image.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Curated templates — IDs match memegen.link template slugs exactly.
# Chosen for versatility in workplace / motivational humour.
# ---------------------------------------------------------------------------
CURATED_TEMPLATES: list[dict[str, str]] = [
    {"id": "drake",       "name": "Drake Hotline Bling",              "use": "Comparing a bad option (top) vs a good option (bottom)"},
    {"id": "doge",        "name": "Doge",                             "use": "Amazement or excitement about something, wow factor"},
    {"id": "db",          "name": "Distracted Boyfriend",             "use": "Being tempted away from what you should be doing"},
    {"id": "balloon",     "name": "Running Away Balloon",             "use": "Something slipping away or being lost"},
    {"id": "batman",      "name": "Batman Slapping Robin",            "use": "Shutting down a bad idea or excuse"},
    {"id": "mordor",      "name": "One Does Not Simply",              "use": "Something that sounds easy but is surprisingly hard"},
    {"id": "buzz",        "name": "X Everywhere (Buzz Lightyear)",    "use": "Something that is everywhere or unavoidable"},
    {"id": "interesting", "name": "The Most Interesting Man",         "use": "Flexing expertise or confidence about a topic"},
    {"id": "astronaut",   "name": "Always Has Been",                  "use": "Revealing that something was always true"},
    {"id": "fine",        "name": "This Is Fine",                     "use": "Pretending everything is okay when it clearly isn't"},
    {"id": "facepalm",    "name": "Facepalm",                         "use": "Reacting to something obviously wrong or frustrating"},
    {"id": "rollsafe",    "name": "Think About It (Roll Safe)",       "use": "Clever loophole or galaxy-brain life hack"},
    {"id": "two-buttons", "name": "Two Buttons",                      "use": "Struggling to choose between two options"},
    {"id": "cmm",         "name": "Change My Mind",                   "use": "Stating a bold or controversial opinion confidently"},
    {"id": "harold",      "name": "Hide the Pain Harold",             "use": "Hiding pain or frustration behind a smile"},
    {"id": "pigeon",      "name": "Is This a Pigeon?",                "use": "Misidentifying something obvious"},
    {"id": "pooh",        "name": "Tuxedo Winnie the Pooh",           "use": "Fancy vs casual way of saying the same thing"},
    {"id": "gru",         "name": "Gru's Plan",                       "use": "A plan that backfires or has an unexpected consequence"},
    {"id": "exit",        "name": "Left Exit 12 Off Ramp",            "use": "Choosing the unexpected or wrong path"},
    {"id": "success",     "name": "Success Kid",                      "use": "Celebrating a small but satisfying win"},
    {"id": "same",        "name": "They're The Same Picture",         "use": "Two things that look different but are actually identical"},
    {"id": "mordor",      "name": "One Does Not Simply",              "use": "Something that sounds easy but is surprisingly hard"},
    {"id": "officespace", "name": "That Would Be Great",              "use": "Passive-aggressive workplace request"},
    {"id": "noidea",      "name": "I Have No Idea What I'm Doing",    "use": "Winging it or faking competence"},
    {"id": "spongebob",   "name": "Mocking Spongebob",                "use": "Sarcastically repeating what someone said"},
    {"id": "stonks",      "name": "Stonks",                            "use": "Making a questionable decision that feels like a win"},
    {"id": "bihw",        "name": "But It's Honest Work",             "use": "Doing something small but feeling proud of it"},
    {"id": "fry",         "name": "Futurama Fry",                     "use": "Not sure if one thing or another — suspicion or doubt"},
    {"id": "headaches",   "name": "Types of Headaches",               "use": "Something causing extreme stress or pain"},
    {"id": "captain",     "name": "I Am the Captain Now",             "use": "Taking charge or asserting dominance"},
    {"id": "dwight",      "name": "Schrute Facts (The Office)",       "use": "Correcting someone in a pedantic, matter-of-fact way"},
    {"id": "wonka",       "name": "Condescending Wonka",              "use": "Sarcastically praising someone's obvious statement"},
    {"id": "morpheus",    "name": "Matrix Morpheus",                  "use": "What if I told you... — revealing a hidden truth"},
    {"id": "spiderman",   "name": "Spider-Man Pointing",              "use": "Two things that are the same pointing at each other"},
    {"id": "kermit",      "name": "But That's None of My Business",   "use": "Making a sly observation while pretending not to care"},
    {"id": "slap",        "name": "Will Smith Slap",                  "use": "Something unexpectedly hitting you hard"},
    {"id": "panik-kalm-panik", "name": "Panik Kalm Panik",           "use": "Panic, brief relief, then panic again"},
]


def get_curated_templates() -> list[dict[str, str]]:
    """Return the curated template list for the LLM to choose from."""
    return CURATED_TEMPLATES


# ---------------------------------------------------------------------------
# URL builder — no HTTP call needed; memegen.link renders on request.
# ---------------------------------------------------------------------------

# Order matters: encode literal underscores before converting spaces to underscores.
_ENCODINGS: list[tuple[str, str]] = [
    ("_",  "__"),   # literal underscore → double underscore
    ("-",  "--"),   # literal dash → double dash
    (" ",  "_"),    # space → underscore
    ("/",  "~s"),
    ("?",  "~q"),
    ("#",  "~h"),
    ("%",  "~p"),
    ("&",  "~a"),
    ('"',  "''"),   # double quote → two single quotes
    ("<",  "~l"),
    (">",  "~g"),
    ("\\", "~b"),
]

_MULTI_UNDERSCORE = re.compile(r"_{3,}")


def _encode_text(text: str) -> str:
    """Encode a caption string for a memegen.link path segment."""
    result = text.strip()
    # Collapse newlines into memegen newline token
    result = re.sub(r"\n+", "~n", result)
    for original, replacement in _ENCODINGS:
        result = result.replace(original, replacement)
    # Three or more underscores shouldn't occur; collapse to double (literal _)
    result = _MULTI_UNDERSCORE.sub("__", result)
    return result or "_"  # path segment must be non-empty


def build_meme_url(
    template_id: str,
    top_text: str,
    bottom_text: str,
    *,
    width: int = 600,
) -> str:
    """Return a ready-to-use memegen.link image URL.

    No HTTP request is needed — the URL itself resolves to the generated image.

    Example:
        build_meme_url("drake", "Writing tests", "Shipping untested code")
        → "https://api.memegen.link/images/drake/Writing_tests/Shipping_untested_code.png?width=600"
    """
    top = _encode_text(top_text)
    bot = _encode_text(bottom_text)
    return f"https://api.memegen.link/images/{template_id}/{top}/{bot}.png?width={width}"
