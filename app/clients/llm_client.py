"""LLM client for classification and filtering (scaffold only)."""

from dataclasses import dataclass

from app.core.config import Settings


@dataclass
class LLMMessage:
    """Chat-style message for future OpenAI-compatible APIs."""

    role: str
    content: str


class LLMClient:
    """Client for OpenAI-compatible endpoints — no network calls in scaffold.

    Intended usage: competitor_filter_service and analysis_service for structured outputs.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def complete(self, messages: list[LLMMessage], *, temperature: float = 0.2) -> str:
        """Send a chat completion request.

        Args:
            messages: Conversation turns.
            temperature: Sampling temperature.

        Returns:
            Model text response.

        Raises:
            NotImplementedError: until real integration is added.
        """
        raise NotImplementedError("LLM integration is deferred to a later iteration.")
