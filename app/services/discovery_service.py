"""Orchestrates competitor discovery from search (Brave + normalization)."""

from app.clients.brave_client import BraveSearchClient


def search_competitors(
    brave_client: BraveSearchClient,
    query: str,
    max_results: int = 10,
) -> list[dict]:
    """Run search and return normalized candidate dicts for the API layer.

    Scaffold: defines the contract only. Real implementation will:
    - call ``brave_client.search_web``
    - map results to internal DTOs / ``CompetitorCandidate`` fields

    Args:
        brave_client: Configured Brave client.
        query: User search string.
        max_results: Upper bound for hits.

    Returns:
        List of plain dicts keyed like API models (url, title, snippet, etc.).
    """
    raise NotImplementedError("Discovery pipeline not wired in scaffold.")
