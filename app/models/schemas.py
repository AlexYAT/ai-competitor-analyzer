"""Pydantic request/response models for the API."""

from pydantic import BaseModel, Field, HttpUrl

from app.models.enums import SiteType


class FindCompetitorsRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query / product description")
    max_results: int = Field(default=10, ge=1, le=50)


class CompetitorCandidate(BaseModel):
    url: HttpUrl
    title: str | None = None
    snippet: str | None = None
    site_type: SiteType | None = Field(
        default=None,
        description="LLM- or rule-based classification (optional in early pipeline).",
    )


class FindCompetitorsResponse(BaseModel):
    query: str
    candidates: list[CompetitorCandidate]


class AnalyzeCompetitorsRequest(BaseModel):
    urls: list[HttpUrl] = Field(..., min_length=1)


class AnalyzeCompetitorsResponse(BaseModel):
    message: str
    analyzed_urls: list[str]
    summary: str | None = None
