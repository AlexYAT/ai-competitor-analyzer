"""Text helpers for normalization and truncation (extend as needed)."""


def truncate(text: str, max_chars: int, suffix: str = "…") -> str:
    """Return ``text`` shortened to ``max_chars`` with optional suffix."""
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - len(suffix))] + suffix
