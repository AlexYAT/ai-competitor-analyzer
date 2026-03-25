"""Market-level report from multiple competitor page analyses."""

import json
from typing import Any

from app.clients.llm_client import LLMClient
from app.core.config import Settings
from app.core.exceptions import ExternalServiceError
from app.models.schemas import MarketReportItem, ReportDemoResponse, ReportSummary
from app.services.analysis_service import analyze_competitor_page
from app.services.parsing_service import parse_page

MARKET_SUMMARY_SYSTEM_PROMPT = """You synthesize a concise MARKET-LEVEL view from several competitor analyses (already extracted as structured fields).

Rules:
- Be practical and product-oriented: positioning, offers, audiences, gaps — not academic prose.
- Base conclusions only on the competitor data provided below. Do not invent brands, metrics, or claims not implied by the input.
- common_strengths: patterns that appear across multiple competitors (or strong recurring themes); short phrases.
- common_weaknesses: recurring gaps or weaknesses; short phrases.
- differentiation_opportunities: concrete ideas for how a new entrant could stand out (messaging, offer, audience slice, UX/motion hooks) grounded in the gaps you see in the data.
- If there is only one competitor, still produce useful summary lists (relative to that single snapshot) and stay tentative where needed.

Output: one JSON object only, no markdown, with exactly these keys:
- market_summary: string (short paragraph, 3–6 sentences)
- common_strengths: array of strings
- common_weaknesses: array of strings
- differentiation_opportunities: array of strings

No extra keys."""


def _req_str(data: dict[str, Any], key: str) -> str:
    val = data.get(key)
    if not isinstance(val, str):
        raise ExternalServiceError(f'LLM report summary: "{key}" must be a string.')
    return val.strip()


def _ensure_str_list(data: dict[str, Any], key: str) -> list[str]:
    val = data.get(key)
    if not isinstance(val, list):
        raise ExternalServiceError(f'LLM report summary: "{key}" must be a JSON array.')
    out: list[str] = []
    for item in val:
        if not isinstance(item, str):
            raise ExternalServiceError(f'LLM report summary: "{key}" must contain only strings.')
        out.append(item.strip())
    return out


def _parse_report_summary_payload(raw: dict[str, Any]) -> ReportSummary:
    return ReportSummary(
        market_summary=_req_str(raw, "market_summary"),
        common_strengths=_ensure_str_list(raw, "common_strengths"),
        common_weaknesses=_ensure_str_list(raw, "common_weaknesses"),
        differentiation_opportunities=_ensure_str_list(raw, "differentiation_opportunities"),
    )


def _build_summary_user_prompt(items: list[MarketReportItem]) -> str:
    rows = []
    for it in items:
        rows.append(
            {
                "title": it.title,
                "positioning": it.positioning,
                "offer": it.offer,
                "target_audience": it.target_audience,
                "strengths": it.strengths,
                "weaknesses": it.weaknesses,
                "design_score": it.design_score,
                "animation_potential": it.animation_potential,
            }
        )
    blob = json.dumps(rows, ensure_ascii=False, indent=2)
    return f"""Competitor analyses (structured JSON array, one object per site):
{blob}

Return only the JSON object specified in the system message."""


def build_market_report(
    urls: list[str],
    settings: Settings,
    llm_client: LLMClient,
) -> ReportDemoResponse:
    """Parse and analyze each URL, then ask the LLM for a cross-competitor summary.

    Raises:
        ExternalServiceError: Invalid LLM summary payload.
        ParsingError: From ``parse_page`` on browser failures (propagated to the route).
    """
    items: list[MarketReportItem] = []
    for url in urls:
        parsed = parse_page(url.strip(), settings)
        analysis = analyze_competitor_page(llm_client, parsed)
        items.append(MarketReportItem.model_validate(analysis.model_dump()))

    summary_raw = llm_client.chat_json(MARKET_SUMMARY_SYSTEM_PROMPT, _build_summary_user_prompt(items))
    summary = _parse_report_summary_payload(summary_raw)
    return ReportDemoResponse(items=items, summary=summary)
