"""Application-level orchestration: reusable from FastAPI and desktop (PyQt) without HTTP.

Thin wrappers around existing services; configuration and external failures surface as
domain exceptions for callers to map to UI or HTTP.
"""

from app.clients.brave_client import BraveSearchClient
from app.clients.llm_client import LLMClient
from app.core.config import Settings
from app.core.exceptions import ConfigurationError, ExternalServiceError
from app.models.schemas import (
    FindCompetitorsRequest,
    FindCompetitorsResponse,
    ReportDemoRequest,
    ReportDemoResponse,
)
from app.services.competitor_filter_service import filter_competitors_with_llm
from app.services.discovery_service import discover_competitors
from app.services.report_service import build_market_report

_BRAVE_KEY_DETAIL = "BRAVE_API_KEY is not configured. Set it in the environment or .env file."
_REPORT_OPENAI_DETAIL = "OPENAI_API_KEY is not configured. Market report requires an LLM API key."


def run_find_competitors(
    settings: Settings,
    brave_client: BraveSearchClient,
    llm_client: LLMClient,
    body: FindCompetitorsRequest,
) -> FindCompetitorsResponse:
    """Discover competitors via Brave, optionally refine with LLM when ``OPENAI_API_KEY`` is set.

    Raises:
        ConfigurationError: Missing Brave API key.
        ExternalServiceError: Brave search or LLM filter failed.
    """
    if not (settings.BRAVE_API_KEY or "").strip():
        raise ConfigurationError(_BRAVE_KEY_DETAIL)

    query_used, raw_results_count, raw_candidates = discover_competitors(
        brave_client,
        niche=body.niche,
        site_type=body.site_type,
        region=body.region,
        count=body.max_results,
    )

    if (settings.OPENAI_API_KEY or "").strip():
        filtered_results = filter_competitors_with_llm(
            llm_client,
            niche=body.niche,
            site_type=body.site_type,
            region=body.region,
            candidates=raw_candidates,
        )
    else:
        filtered_results = raw_candidates

    return FindCompetitorsResponse(
        query_used=query_used,
        raw_results_count=raw_results_count,
        filtered_results=filtered_results,
    )


def run_report_demo(
    settings: Settings,
    llm_client: LLMClient,
    body: ReportDemoRequest,
) -> ReportDemoResponse:
    """Build market report: parse + per-URL analysis + cross-competitor summary.

    Raises:
        ConfigurationError: Missing OpenAI (LLM) API key.
    """
    if not (settings.OPENAI_API_KEY or "").strip():
        raise ConfigurationError(_REPORT_OPENAI_DETAIL)

    return build_market_report(body.urls, settings, llm_client, lang=body.lang)
