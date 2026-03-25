"""Competitor discovery and analysis API (stub implementations)."""

from fastapi import APIRouter

from app.models.schemas import (
    AnalyzeCompetitorsRequest,
    AnalyzeCompetitorsResponse,
    CompetitorCandidate,
    FindCompetitorsRequest,
    FindCompetitorsResponse,
)
from app.models.enums import SiteType

router = APIRouter(tags=["competitors"])


@router.post("/find-competitors", response_model=FindCompetitorsResponse)
def find_competitors(body: FindCompetitorsRequest) -> FindCompetitorsResponse:
    """Stub: returns mock candidates. Real flow will use Brave + discovery service."""
    mock_candidates = [
        CompetitorCandidate(
            url="https://example-competitor-a.com",
            title=f"Mock result for: {body.query}",
            snippet="Placeholder snippet from scaffold.",
            site_type=SiteType.multi_page_service_site,
        ),
        CompetitorCandidate(
            url="https://example-competitor-b.com",
            title=f"Another mock for: {body.query}",
            snippet="Second placeholder result.",
            site_type=SiteType.landing,
        ),
    ]
    return FindCompetitorsResponse(
        query=body.query,
        candidates=mock_candidates,
    )


@router.post("/analyze-competitors", response_model=AnalyzeCompetitorsResponse)
def analyze_competitors(body: AnalyzeCompetitorsRequest) -> AnalyzeCompetitorsResponse:
    """Stub: placeholder for future parsing + AI analysis pipeline."""
    return AnalyzeCompetitorsResponse(
        message="Analysis not implemented yet (scaffold).",
        analyzed_urls=list(body.urls),
        summary=None,
    )
