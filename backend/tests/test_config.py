"""Tests for the settings layer."""
from __future__ import annotations


def test_chat_completions_url(settings):
    assert settings.chat_completions_url == (
        "https://fake.openai.azure.com/openai/deployments/gpt-4o-mini"
        "/chat/completions?api-version=2025-01-01-preview"
    )


def test_origins_list(settings):
    assert settings.origins_list == ["http://localhost:5173"]
