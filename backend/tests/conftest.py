"""Shared pytest fixtures for the backend."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Provide deterministic config *before* the app imports settings.
os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://fake.openai.azure.com")
os.environ.setdefault("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
os.environ.setdefault("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
os.environ.setdefault("AZURE_OPENAI_API_KEY", "test-key")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")


@pytest.fixture
def settings():
    from app.config import get_settings

    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
def client():
    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c
