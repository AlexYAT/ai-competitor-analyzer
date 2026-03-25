"""Orchestration use-cases without HTTP (desktop / shared layer)."""

from typing import Any

import pytest

from app.clients.brave_client import BraveSearchClient
from app.clients.llm_client import LLMClient
from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.models.enums import SiteType
from app.models.schemas import FindCompetitorsRequest, ReportDemoRequest
from app.services.orchestration import run_find_competitors, run_report_demo


def test_run_find_competitors_raises_configuration_error_without_brave_key() -> None:
    settings = Settings(
        BRAVE_API_KEY="",
        BRAVE_BASE_URL="https://api.search.brave.com/res/v1/web/search",
        HTTP_TIMEOUT=20.0,
    )
    body = FindCompetitorsRequest(niche="test", site_type=SiteType.blog, max_results=3)
    brave = BraveSearchClient(settings)
    llm = LLMClient(settings)

    with pytest.raises(ConfigurationError, match="BRAVE_API_KEY"):
        run_find_competitors(settings, brave, llm, body)


def test_run_report_demo_raises_configuration_error_without_openai_key() -> None:
    settings = Settings(
        BRAVE_API_KEY="key",
        BRAVE_BASE_URL="https://api.search.brave.com/res/v1/web/search",
        HTTP_TIMEOUT=20.0,
        OPENAI_API_KEY="",
    )
    body = ReportDemoRequest(urls=["https://example.com"])
    llm = LLMClient(settings)

    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
        run_report_demo(settings, llm, body)


def _mock_brave_payload() -> dict[str, Any]:
    return {
        "web": {
            "results": [
                {"title": "One", "url": "https://one.example/", "description": "d"},
            ]
        }
    }


class _FakeBrave:
    def search_web(self, query: str, count: int = 10) -> dict[str, Any]:
        return _mock_brave_payload()


def test_run_find_competitors_returns_response_when_brave_configured() -> None:
    settings = Settings(
        BRAVE_API_KEY="sk-brave",
        BRAVE_BASE_URL="https://api.search.brave.com/res/v1/web/search",
        HTTP_TIMEOUT=20.0,
        OPENAI_API_KEY="",
    )
    body = FindCompetitorsRequest(niche="widgets", site_type=SiteType.landing, max_results=5)
    llm = LLMClient(settings)

    out = run_find_competitors(settings, _FakeBrave(), llm, body)  # type: ignore[arg-type]

    assert out.raw_results_count == 1
    assert len(out.filtered_results) == 1
    assert out.filtered_results[0].url == "https://one.example/"
    assert "widgets" in out.query_used
