"""URL normalization helpers."""


def normalize_url(url: str) -> str:
    """Best-effort canonical form (scaffold: strip trailing slash only)."""
    return url.rstrip("/")
