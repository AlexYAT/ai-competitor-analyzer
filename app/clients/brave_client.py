"""Brave Search API client (scaffold only; no HTTP calls yet)."""

from dataclasses import dataclass

from app.core.config import Settings


@dataclass
class BraveSearchResult:
    """Single search hit placeholder; shape will align with Brave API when implemented."""

    url: str
    title: str | None
    description: str | None


class BraveSearchClient:
    """Thin wrapper for Brave Search — configure with API key, implement queries later.

    Intended usage: discovery_service calls this to fetch raw SERP-style results.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def search_web(self, query: str, count: int = 10) -> list[BraveSearchResult]:
        """Execute a web search via Brave API.

        Returns:
            List of raw results. Not implemented in scaffold.

        Raises:
            NotImplementedError: until real integration is added.
        """
        raise NotImplementedError("Brave Search integration is deferred to a later iteration.")
