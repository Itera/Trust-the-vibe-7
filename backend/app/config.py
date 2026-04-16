"""Runtime configuration loaded from backend/.env (with priority over shell env)."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent

# The .env location can be overridden (e.g. in tests) by setting BACKEND_ENV_FILE.
ENV_FILE = Path(os.environ.get("BACKEND_ENV_FILE", str(BACKEND_DIR / ".env")))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    azure_openai_endpoint: str = Field(..., alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: str = Field("gpt-4o-mini", alias="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str = Field(
        "2025-01-01-preview", alias="AZURE_OPENAI_API_VERSION"
    )
    azure_openai_api_key: str = Field(..., alias="AZURE_OPENAI_API_KEY")

    # Optional: enables the 'video' + 'mood_board' card kinds via Pixabay.
    pixabay_api_key: str | None = Field(default=None, alias="PIXABAY_API_KEY")

    allowed_origins: str = Field(
        "http://localhost:5173,http://127.0.0.1:5173", alias="ALLOWED_ORIGINS"
    )

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def chat_completions_url(self) -> str:
        base = self.azure_openai_endpoint.rstrip("/")
        return (
            f"{base}/openai/deployments/{self.azure_openai_deployment}"
            f"/chat/completions?api-version={self.azure_openai_api_version}"
        )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Give the project's .env file priority over shell env vars so users
        # whose shell happens to export AZURE_OPENAI_API_KEY don't silently
        # override the project config.
        return (init_settings, dotenv_settings, env_settings, file_secret_settings)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
