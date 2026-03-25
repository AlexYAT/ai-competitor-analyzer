"""Application configuration from environment."""

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _coerce_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "yes", "on")
    return bool(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BRAVE_API_KEY: str = ""
    BRAVE_BASE_URL: str = "https://api.search.brave.com/res/v1/web/search"
    HTTP_TIMEOUT: float = 20.0

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    SELENIUM_HEADLESS: bool = True
    SELENIUM_PAGELOAD_TIMEOUT: int = 15
    SELENIUM_WAIT_TIMEOUT: int = 10
    PARSED_SCREENSHOTS_DIR: str = "data/screenshots"

    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    @field_validator("SELENIUM_HEADLESS", mode="before")
    @classmethod
    def _selenium_headless_bool(cls, v: Any) -> bool:
        return _coerce_bool(v)


@lru_cache
def get_settings() -> Settings:
    return Settings()
