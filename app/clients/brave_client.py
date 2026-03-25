"""Brave Search API client."""

import logging
from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


class BraveSearchClient:
    """HTTP client for Brave Web Search (REST v1).

    Uses ``X-Subscription-Token`` authentication and returns the parsed JSON body
    as a plain ``dict`` matching the API response shape (``web.results``, etc.).
    """

    def __init__(self, settings: Settings) -> None:
        self._api_key = (settings.BRAVE_API_KEY or "").strip()
        self._base_url = settings.BRAVE_BASE_URL.strip()
        self._timeout = float(settings.HTTP_TIMEOUT)

    def search_web(self, query: str, count: int = 10) -> dict[str, Any]:
        """Call Brave ``GET /res/v1/web/search`` and return the JSON object.

        Args:
            query: Search query string (``q``).
            count: Maximum number of results to request.

        Returns:
            Parsed JSON response from Brave.

        Raises:
            ExternalServiceError: On network failure, non-success HTTP status, or invalid JSON.
        """
        if not self._api_key:
            raise ExternalServiceError("Brave API key is missing; cannot call search.")

        headers = {"X-Subscription-Token": self._api_key, "Accept": "application/json"}
        params = {"q": query, "count": count}

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(self._base_url, headers=headers, params=params)
        except httpx.RequestError as exc:
            logger.warning("Brave Search request error: %s", exc)
            raise ExternalServiceError(f"Brave Search request failed: {exc}") from exc

        if response.status_code >= 400:
            body = (response.text or "")[:500]
            logger.warning(
                "Brave Search HTTP %s: %s",
                response.status_code,
                body,
            )
            raise ExternalServiceError(
                f"Brave Search returned HTTP {response.status_code}. {body}".strip()
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise ExternalServiceError("Brave Search returned invalid JSON.") from exc

        if not isinstance(payload, dict):
            raise ExternalServiceError("Brave Search response is not a JSON object.")

        return payload
