"""Pydantic request/response models for the API."""

from pydantic import BaseModel, Field, HttpUrl

from app.models.enums import SiteType


class FindCompetitorsRequest(BaseModel):
    niche: str = Field(..., min_length=1, description="Niche / product / service wording for search")
    site_type: SiteType = Field(..., description="Target site shape to include in the built query")
    region: str | None = Field(default=None, description="Optional region or country name")
    max_results: int = Field(default=10, ge=1, le=50)


class CompetitorCandidate(BaseModel):
    title: str = Field(..., description="Result title from search")
    url: str = Field(..., description="Canonical result URL")
    description: str = Field(default="", description="Snippet / description from search")
    site_type: SiteType
    source: str = Field(..., description="Origin of the hit, e.g. brave")


class FindCompetitorsResponse(BaseModel):
    query_used: str
    raw_results_count: int
    filtered_results: list[CompetitorCandidate]


class AnalyzeCompetitorsRequest(BaseModel):
    urls: list[HttpUrl] = Field(..., min_length=1)


class AnalyzeCompetitorsResponse(BaseModel):
    message: str
    analyzed_urls: list[str]
    summary: str | None = None
