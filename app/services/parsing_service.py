"""Fetch and parse HTML / structured content from selected competitor URLs."""

from typing import Any


def fetch_page_text(url: str, timeout_seconds: float = 30.0) -> str:
    """Download page and extract main text (no Selenium; HTTP + parser when built).

    Args:
        url: Target URL.
        timeout_seconds: Request timeout.

    Returns:
        Extracted plain text.

    Raises:
        NotImplementedError: scaffold only.
    """
    raise NotImplementedError("Parsing not implemented in scaffold.")


def parse_metadata(url: str) -> dict[str, Any]:
    """Extract title, meta description, headings, etc."""
    raise NotImplementedError("Metadata parsing not implemented in scaffold.")
