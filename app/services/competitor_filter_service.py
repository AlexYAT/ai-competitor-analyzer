"""LLM-based relevance filtering and site type classification."""

from app.clients.llm_client import LLMClient
from app.models.enums import SiteType


def filter_relevant_sites(
    llm_client: LLMClient,
    candidates: list[dict],
) -> list[dict]:
    """Use an LLM to drop irrelevant URLs and optionally set ``site_type``.

    Scaffold: signature only. Future version will:
    - build a structured prompt with URLs/snippets
    - parse JSON or tool output into filtered list

    Args:
        llm_client: LLM client.
        candidates: Raw or search-normalized candidates.

    Returns:
        Subset of candidates marked relevant with optional ``SiteType``.
    """
    raise NotImplementedError("LLM filtering not wired in scaffold.")


def classify_site_type(llm_client: LLMClient, url: str, snippet: str | None) -> SiteType:
    """Classify a single URL into ``SiteType`` (future implementation)."""
    raise NotImplementedError("Site classification not wired in scaffold.")
