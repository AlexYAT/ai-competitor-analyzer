"""AI analysis of a parsed competitor page (LLM, text-only)."""

from typing import Any

from app.clients.llm_client import LLMClient
from app.core.exceptions import ExternalServiceError
from app.models.schemas import CompetitorAnalysisResult, ParsedPageData

ANALYSIS_SYSTEM_PROMPT = """You analyze a single competitor landing page using ONLY the text fields provided.
Be practical and concise, not academic.

Rules:
- Do not invent facts, company names, metrics, or claims that are not supported by the input.
- If the input is sparse, state uncertainty briefly and keep judgments tentative.
- strengths and weaknesses must be short bullet phrases (no more than ~120 chars each), grounded in the text.
- design_score: subjective 0–10 inferred from structure, clarity of offer, headings, and how polished the page feels from the TEXT alone (not from images or real screenshots).
- animation_potential: 0–10 for how much the page could benefit from motion, micro-interactions, or stronger visual storytelling (still inferred from text structure and messaging gaps only).

Output: a single JSON object with exactly these keys and types:
- positioning: string
- offer: string
- target_audience: string
- strengths: array of strings
- weaknesses: array of strings
- design_score: number between 0 and 10
- animation_potential: number between 0 and 10
- summary: string (2–4 sentences)

No markdown, no code fences, no extra keys."""


def _req_str(data: dict[str, Any], key: str) -> str:
    val = data.get(key)
    if not isinstance(val, str):
        raise ExternalServiceError(f'LLM response: "{key}" must be a string.')
    return val.strip()


def _ensure_str_list(data: dict[str, Any], key: str) -> list[str]:
    val = data.get(key)
    if not isinstance(val, list):
        raise ExternalServiceError(f'LLM response: "{key}" must be a JSON array.')
    out: list[str] = []
    for item in val:
        if not isinstance(item, str):
            raise ExternalServiceError(f'LLM response: "{key}" must contain only strings.')
        out.append(item.strip())
    return out


def _score_0_10(data: dict[str, Any], key: str) -> float:
    raw = data.get(key)
    try:
        x = float(raw)
    except (TypeError, ValueError):
        raise ExternalServiceError(f'LLM response: "{key}" must be a number.') from None
    return max(0.0, min(10.0, x))


def _build_user_prompt(parsed: ParsedPageData) -> str:
    meta = parsed.meta_description or "(none)"
    h1 = parsed.h1 or "(none)"
    return f"""Analyze this page.

final_url: {parsed.final_url}
title: {parsed.title}
meta_description: {meta}
h1: {h1}

visible_text:
{parsed.visible_text}

Return only the JSON object as specified in the system message."""


def analyze_competitor_page(
    llm_client: LLMClient,
    parsed_page: ParsedPageData,
) -> CompetitorAnalysisResult:
    """Run LLM analysis on parsed text fields and return a structured result.

    Raises:
        ExternalServiceError: On bad LLM JSON or invalid field types.
    """
    raw = llm_client.chat_json(ANALYSIS_SYSTEM_PROMPT, _build_user_prompt(parsed_page))

    positioning = _req_str(raw, "positioning")
    offer = _req_str(raw, "offer")
    target_audience = _req_str(raw, "target_audience")
    strengths = _ensure_str_list(raw, "strengths")
    weaknesses = _ensure_str_list(raw, "weaknesses")
    design_score = _score_0_10(raw, "design_score")
    animation_potential = _score_0_10(raw, "animation_potential")
    summary = _req_str(raw, "summary")

    return CompetitorAnalysisResult(
        url=parsed_page.requested_url,
        final_url=parsed_page.final_url,
        title=parsed_page.title,
        positioning=positioning,
        offer=offer,
        target_audience=target_audience,
        strengths=strengths,
        weaknesses=weaknesses,
        design_score=design_score,
        animation_potential=animation_potential,
        summary=summary,
    )


def compare_competitors(insights: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-site insights into a comparison view."""
    raise NotImplementedError("Comparison not implemented in scaffold.")
