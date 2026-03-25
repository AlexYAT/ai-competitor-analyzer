"""AI analysis of competitor content (positioning, features, gaps)."""

from typing import Any


def analyze_competitor_page(
    url: str,
    page_text: str,
) -> dict[str, Any]:
    """Run LLM analysis on extracted text for one competitor.

    Returns:
        Structured insights (TBD schema).
    """
    raise NotImplementedError("AI analysis not implemented in scaffold.")


def compare_competitors(insights: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-site insights into a comparison view."""
    raise NotImplementedError("Comparison not implemented in scaffold.")
