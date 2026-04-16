"""Pydantic models for the HuMotivatoren API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Language = Literal["en", "no"]
PersonaKey = Literal["consultant", "stoic", "nordmann", "gremlin"]

# The set of card kinds the frontend knows how to render. Unknown kinds
# degrade gracefully in the UI so a team member can add one in a single PR.
CardKind = Literal[
    "peptalk",
    "quote",
    "fact",
    "kpi",
    "advice",
    "image",
    "number_trivia",
    "haiku",
    "horoscope",
    "playlist",
    "testimonial",
    "recommendation",
]

DEFAULT_CARDS: list[CardKind] = [
    "peptalk",
    "quote",
    "fact",
    "kpi",
    "advice",
    "image",
    "haiku",
    "recommendation",
]


class MotivationRequest(BaseModel):
    task: str = Field(..., min_length=1, max_length=500)
    persona: PersonaKey = "consultant"
    language: Language = "en"
    seriousness: int = Field(30, ge=0, le=100)
    cards: list[CardKind] = Field(default_factory=lambda: list(DEFAULT_CARDS))


class Card(BaseModel):
    kind: CardKind
    title: str
    body: str
    attribution: str | None = None  # e.g. "— Seneca"
    image_url: str | None = None  # for `image` cards
    source: str | None = None  # which API or persona produced it


class UiTheme(BaseModel):
    background: str | None = None
    accent: str | None = None
    fontScale: float | None = None


class MotivationPackage(BaseModel):
    task: str
    persona: PersonaKey
    language: Language
    report_title: str  # "MOTIVATION DOSE • Q2-2026 REPORT"
    report_subtitle: str  # short editorial line in persona voice
    cards: list[Card]
    ui: UiTheme | None = None


class PersonaSummary(BaseModel):
    key: PersonaKey
    name: str
    tagline: str
    accent_color: str
