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


class ParseDemoRequest(BaseModel):
    url: str = Field(..., min_length=1, description="Page URL to open in the browser")


class ParsedPageData(BaseModel):
    requested_url: str
    final_url: str
    title: str
    meta_description: str | None
    h1: str | None
    visible_text: str
    screenshot_path: str | None


class ParseDemoResponse(BaseModel):
    result: ParsedPageData


class CompetitorAnalysisRequest(BaseModel):
    url: str = Field(..., min_length=1, description="Page URL to fetch and analyze")
    use_parsing: bool = Field(default=True, description="When true, Selenium fetch runs first (v1 only supports true)")


class CompetitorAnalysisResult(BaseModel):
    url: str
    final_url: str
    title: str
    positioning: str
    offer: str
    target_audience: str
    strengths: list[str]
    weaknesses: list[str]
    design_score: float = Field(..., ge=0.0, le=10.0, description="0–10: inferred visual polish from text structure and offer")
    animation_potential: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="0–10: room to improve via motion / dynamic presentation",
    )
    summary: str


class CompetitorAnalysisResponse(BaseModel):
    result: CompetitorAnalysisResult


class ReportDemoRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, description="Competitor page URLs to parse and analyze")


class MarketReportItem(BaseModel):
    url: str
    final_url: str
    title: str
    positioning: str
    offer: str
    target_audience: str
    strengths: list[str]
    weaknesses: list[str]
    design_score: float = Field(..., ge=0.0, le=10.0)
    animation_potential: float = Field(..., ge=0.0, le=10.0)
    summary: str


class ReportSummary(BaseModel):
    market_summary: str
    common_strengths: list[str]
    common_weaknesses: list[str]
    differentiation_opportunities: list[str]


class ReportDemoResponse(BaseModel):
    items: list[MarketReportItem]
    summary: ReportSummary
