"""Shared pytest fixtures for the backend."""
from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# Point at a path that does not exist so the real backend/.env never leaks
# into the test process. Must be set *before* app.config is imported.
os.environ["BACKEND_ENV_FILE"] = os.path.join(
    tempfile.gettempdir(), "trust-the-vibe-7-tests-no-env.env"
)

# Provide deterministic config that will be picked up from the shell env.
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://fake.openai.azure.com"
os.environ["AZURE_OPENAI_DEPLOYMENT"] = "gpt-4o-mini"
os.environ["AZURE_OPENAI_API_VERSION"] = "2025-01-01-preview"
os.environ["AZURE_OPENAI_API_KEY"] = "test-key"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:5173"


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
