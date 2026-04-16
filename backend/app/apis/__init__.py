"""Clients for the free third-party APIs that feed HuMotivatoren."""
from .advice import fetch_advice
from .facts import fetch_useless_fact
from .images import fetch_cat_image
from .numbers import fetch_number_trivia
from .pixabay import fetch_images as fetch_pixabay_images
from .pixabay import fetch_video as fetch_pixabay_video
from .quotes import fetch_quote

__all__ = [
    "fetch_advice",
    "fetch_useless_fact",
    "fetch_cat_image",
    "fetch_number_trivia",
    "fetch_quote",
    "fetch_pixabay_images",
    "fetch_pixabay_video",
]
