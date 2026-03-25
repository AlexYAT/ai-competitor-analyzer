"""Competitor discovery and analysis API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_brave_client, get_llm_client
from app.clients.brave_client import BraveSearchClient
from app.clients.llm_client import LLMClient
from app.core.config import Settings, get_settings
from app.core.exceptions import ExternalServiceError, ParsingError
from app.models.schemas import (
    AnalyzeCompetitorsRequest,
    AnalyzeCompetitorsResponse,
    CompetitorAnalysisRequest,
    CompetitorAnalysisResponse,
    FindCompetitorsRequest,
    FindCompetitorsResponse,
    ParseDemoRequest,
    ParseDemoResponse,
    ReportDemoRequest,
    ReportDemoResponse,
)
from app.services.analysis_service import analyze_competitor_page
from app.services.competitor_filter_service import filter_competitors_with_llm
from app.services.discovery_service import discover_competitors
from app.services.parsing_service import parse_page
from app.services.report_service import build_market_report

router = APIRouter(tags=["competitors"])


@router.post("/find-competitors", response_model=FindCompetitorsResponse)
def find_competitors(
    body: FindCompetitorsRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    brave_client: Annotated[BraveSearchClient, Depends(get_brave_client)],
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
) -> FindCompetitorsResponse:
    """Discover via Brave Search, then optionally refine with LLM (skipped without OPENAI_API_KEY)."""
    if not (settings.BRAVE_API_KEY or "").strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BRAVE_API_KEY is not configured. Set it in the environment or .env file.",
        )

    try:
        query_used, raw_results_count, raw_candidates = discover_competitors(
            brave_client,
            niche=body.niche,
            site_type=body.site_type,
            region=body.region,
            count=body.max_results,
        )
    except ExternalServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    if (settings.OPENAI_API_KEY or "").strip():
        try:
            filtered_results = filter_competitors_with_llm(
                llm_client,
                niche=body.niche,
                site_type=body.site_type,
                region=body.region,
                candidates=raw_candidates,
            )
        except ExternalServiceError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc
    else:
        filtered_results = raw_candidates

    return FindCompetitorsResponse(
        query_used=query_used,
        raw_results_count=raw_results_count,
        filtered_results=filtered_results,
    )


@router.post("/parsedemo", response_model=ParseDemoResponse)
def parse_demo(
    body: ParseDemoRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ParseDemoResponse:
    """Demo: Selenium fetch — title, meta description, h1, visible text, screenshot."""
    try:
        result = parse_page(body.url, settings)
    except ParsingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    return ParseDemoResponse(result=result)


@router.post("/analyze-competitor", response_model=CompetitorAnalysisResponse)
def analyze_competitor(
    body: CompetitorAnalysisRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
) -> CompetitorAnalysisResponse:
    """Fetch page via Selenium, then LLM analysis (text fields only; no vision)."""
    if not (settings.OPENAI_API_KEY or "").strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY is not configured. AI analysis requires an LLM API key.",
        )
    if not body.use_parsing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="use_parsing=false is not supported in v1; supply use_parsing=true.",
        )

    try:
        parsed = parse_page(body.url, settings)
    except ParsingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    try:
        result = analyze_competitor_page(llm_client, parsed)
    except ExternalServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return CompetitorAnalysisResponse(result=result)


@router.post("/reportdemo", response_model=ReportDemoResponse)
def report_demo(
    body: ReportDemoRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
) -> ReportDemoResponse:
    """Build a market-level report: parse + per-URL analysis, then cross-competitor LLM summary."""
    if not (settings.OPENAI_API_KEY or "").strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY is not configured. Market report requires an LLM API key.",
        )

    try:
        return build_market_report(body.urls, settings, llm_client)
    except ParsingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except ExternalServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.post("/analyze-competitors", response_model=AnalyzeCompetitorsResponse)
def analyze_competitors(body: AnalyzeCompetitorsRequest) -> AnalyzeCompetitorsResponse:
    """Stub: placeholder for future parsing + AI analysis pipeline."""
    return AnalyzeCompetitorsResponse(
        message="Analysis not implemented yet (scaffold).",
        analyzed_urls=[str(u) for u in body.urls],
        summary=None,
    )
