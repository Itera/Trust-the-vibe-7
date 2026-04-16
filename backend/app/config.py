"""Runtime configuration loaded from environment (and backend/.env)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    azure_openai_endpoint: str = Field(..., alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: str = Field("gpt-4o-mini", alias="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_version: str = Field(
        "2025-01-01-preview", alias="AZURE_OPENAI_API_VERSION"
    )
    azure_openai_api_key: str = Field(..., alias="AZURE_OPENAI_API_KEY")

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


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
