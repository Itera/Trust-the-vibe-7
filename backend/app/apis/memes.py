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
    {"id": "drake",       "name": "Drake Hotline Bling",              "use": "Comparing a bad option (top) vs a good option (bottom). Format: top = the wrong/boring choice, bottom = the clearly superior alternative. Great for 'doing X vs doing Y' contrasts. Tone: smug, self-aware."},
    {"id": "doge",        "name": "Doge",                             "use": "Pure amazement or childlike excitement. Top text scattered around: 'wow', 'such X', 'very Y', 'much Z'. Best for celebrating something surprisingly cool or absurdly impressive. Tone: wholesome, enthusiastic."},
    {"id": "db",          "name": "Distracted Boyfriend",             "use": "Being tempted away from what you should be doing. Top = the shiny distraction, bottom = the neglected responsibility. Perfect for procrastination or shifting priorities. Tone: guilty, relatable."},
    {"id": "balloon",     "name": "Running Away Balloon",             "use": "Something important slipping away while you watch helplessly. Top = the thing escaping, bottom = you failing to hold on. Good for missed deadlines, lost motivation, or fading plans. Tone: wistful, mildly tragic."},
    {"id": "batman",      "name": "Batman Slapping Robin",            "use": "Brutally shutting down a bad idea, excuse, or complaint. Top = the dumb thing someone says, bottom = the sharp rebuttal. Best when the correction is blunt and satisfying. Tone: aggressive, cathartic."},
    {"id": "mordor",      "name": "One Does Not Simply",              "use": "Something that sounds easy but is deceptively hard. Format: 'One does not simply [do X]'. Perfect for underestimated tasks, tricky processes, or things people naively attempt. Tone: wise, dramatic."},
    {"id": "buzz",        "name": "X Everywhere (Buzz Lightyear)",    "use": "Something that's suddenly everywhere or unavoidable. Format: top = '[X]', bottom = '[X] everywhere'. Great for trends, buzzwords, or things flooding your feed/inbox. Tone: overwhelmed, amused."},
    {"id": "interesting", "name": "The Most Interesting Man",         "use": "Flexing quiet confidence or niche expertise. Format: 'I don't always [X], but when I do, [Y]'. Best for humblebrag or ironic self-praise. Tone: suave, deadpan cool."},
    {"id": "astronaut",   "name": "Always Has Been",                  "use": "Revealing something was always true — the shocking non-twist. Format: 'Wait, it's all [X]?' / 'Always has been.' Perfect for obvious truths people are slow to realize. Tone: existential, darkly funny."},
    {"id": "fine",        "name": "This Is Fine",                     "use": "Pretending everything is okay while surrounded by disaster. One-liner works best: the situation that's clearly NOT fine. Perfect for overwhelming workloads, chaos, or denial. Tone: forced calm, existential dread."},
    {"id": "facepalm",    "name": "Facepalm",                         "use": "Reacting to something obviously wrong, frustrating, or embarrassing. Best for stupid mistakes, avoidable errors, or 'how did no one catch this' moments. Tone: exasperated, disbelief."},
    {"id": "rollsafe",    "name": "Think About It (Roll Safe)",       "use": "A galaxy-brain loophole or life hack that's technically correct but absurd. Format: 'Can't [have problem X] if you [ridiculous solution Y]'. Tone: smug genius, tapping-head energy."},
    {"id": "two-buttons", "name": "Two Buttons",                      "use": "Struggling to choose between two options, sweating over the decision. Both options should feel equally tempting or equally bad. Tone: anxious, paralyzed by choice."},
    {"id": "cmm",         "name": "Change My Mind",                   "use": "Stating a bold, confident opinion and daring anyone to disagree. Format: '[Hot take]. Change my mind.' Best for strong but defensible (or hilariously indefensible) opinions. Tone: calm provocation."},
    {"id": "harold",      "name": "Hide the Pain Harold",             "use": "Smiling through pain, frustration, or disappointment. The gap between the smile and the suffering IS the joke. Best for situations where you have to pretend you're fine. Tone: forced cheerfulness, inner agony."},
    {"id": "pigeon",      "name": "Is This a Pigeon?",                "use": "Hilariously misidentifying something obvious. Format: person = [who], butterfly = [the thing], caption = 'Is this [wrong label]?'. Perfect for people confusing basic concepts. Tone: clueless, innocent."},
    {"id": "pooh",        "name": "Tuxedo Winnie the Pooh",           "use": "The fancy vs casual version of the same thing. Top = the basic/normal way, bottom = the refined/pretentious version. Great for elevating mundane tasks. Tone: sophisticated, snobby."},
    {"id": "gru",         "name": "Gru's Plan",                       "use": "A plan that seems great until the last step backfires. The final panel is the unexpected bad consequence you didn't think through. Tone: dawning horror, comedic self-sabotage."},
    {"id": "exit",        "name": "Left Exit 12 Off Ramp",            "use": "Choosing the unexpected, wrong, or chaotic path over the sensible one. Straight road = the responsible choice, exit = the impulsive one. Tone: reckless, zero regrets."},
    {"id": "success",     "name": "Success Kid",                      "use": "Celebrating a small but satisfying victory. Best for minor wins that feel disproportionately good — finishing a task, fixing a bug, surviving a meeting. Tone: triumphant, fist-pump energy."},
    {"id": "same",        "name": "They're The Same Picture",         "use": "Two things that look different but are actually identical. Format: show two 'different' things, then 'They're the same picture.' Perfect for exposing false distinctions. Tone: deadpan, corporate Pam energy."},
    {"id": "officespace", "name": "That Would Be Great",              "use": "A passive-aggressive workplace request dripping with faux politeness. Format: 'Yeah, if you could [thing], that would be great.' Best for tedious asks. Tone: micro-managing, soul-crushing."},
    {"id": "noidea",      "name": "I Have No Idea What I'm Doing",    "use": "Winging it, faking competence, or being thrown into the deep end. Best for imposter syndrome, learning on the job, or pretending to know what's going on. Tone: cheerful incompetence."},
    {"id": "spongebob",   "name": "Mocking Spongebob",                "use": "Sarcastically repeating what someone said in aLtErNaTiNg CaSe. Top = the original statement, bottom = the mocking version. Best for dismissing bad takes. Tone: savage, petty."},
    {"id": "stonks",      "name": "Stonks",                            "use": "Making a questionable decision that feels like a genius move. The 'success' is dubious at best. Perfect for bad-but-confident choices. Tone: delusional optimism."},
    {"id": "bihw",        "name": "But It's Honest Work",             "use": "Doing something tiny or unglamorous but feeling quietly proud. Best for small contributions, thankless tasks, or minimal-effort achievements. Tone: humble, dignified."},
    {"id": "fry",         "name": "Futurama Fry",                     "use": "Suspicious squinting — not sure if one thing or another. Format: 'Not sure if [X] or [Y]'. Perfect for ambiguous situations or mixed signals. Tone: skeptical, paranoid."},
    {"id": "headaches",   "name": "Types of Headaches",               "use": "Something causing extreme, specific stress or pain — worse than any normal headache. The thing IS the headache. Best for frustrating tools, processes, or people. Tone: suffering, dramatic."},
    {"id": "captain",     "name": "I Am the Captain Now",             "use": "Taking charge, asserting unexpected dominance, or seizing control of a situation. Best for power shifts or stepping up. Tone: assertive, no-nonsense."},
    {"id": "dwight",      "name": "Schrute Facts (The Office)",       "use": "Pedantically correcting someone with an 'actually' energy. Format: state a 'fact' in a matter-of-fact, slightly condescending way. Tone: know-it-all, insufferable."},
    {"id": "wonka",       "name": "Condescending Wonka",              "use": "Sarcastically patronizing someone's obvious or naive statement. Format: 'Oh, you [did obvious thing]? You must be [sarcastic praise].' Tone: dripping condescension."},
    {"id": "morpheus",    "name": "Matrix Morpheus",                  "use": "Revealing a hidden truth or reframing reality. Format: 'What if I told you [mind-blowing reframe]'. Best for challenging assumptions. Tone: philosophical, red-pill energy."},
    {"id": "spiderman",   "name": "Spider-Man Pointing",              "use": "Two identical things pointing at each other, not realizing they're the same. Perfect for teams blaming each other or duplicate efforts. Tone: confused, ironic."},
    {"id": "kermit",      "name": "But That's None of My Business",   "use": "Making a sly, judgmental observation while pretending not to care. Format: '[Observation]... but that's none of my business.' Best for passive-aggressive shade. Tone: sipping tea, unbothered."},
    {"id": "slap",        "name": "Will Smith Slap",                  "use": "Something unexpectedly hitting you hard — emotionally, mentally, or professionally. The slap comes out of nowhere. Best for sudden bad news or reality checks. Tone: shocked, blindsided."},
    {"id": "panik-kalm-panik", "name": "Panik Kalm Panik",           "use": "Three-beat emotional rollercoaster: panic about X, brief relief from Y, then panic again because of Z. The final panic should be worse or funnier. Tone: spiraling anxiety."},
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
