"""Shared FastAPI dependencies (DI hooks for services and clients)."""

from typing import Annotated

from fastapi import Depends

from app.clients.brave_client import BraveSearchClient
from app.clients.llm_client import LLMClient
from app.core.config import Settings, get_settings


def get_brave_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> BraveSearchClient:
    return BraveSearchClient(settings=settings)


def get_llm_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> LLMClient:
    return LLMClient(settings=settings)
