"""Clients for the free third-party APIs that feed HuMotivatoren."""
from .advice import fetch_advice
from .facts import fetch_useless_fact
from .images import fetch_cat_image
from .memes import build_meme_url, get_curated_templates
from .numbers import fetch_number_trivia
from .quotes import fetch_quote

__all__ = [
    "fetch_advice",
    "fetch_useless_fact",
    "fetch_cat_image",
    "build_meme_url",
    "get_curated_templates",
    "fetch_number_trivia",
    "fetch_quote",
]
