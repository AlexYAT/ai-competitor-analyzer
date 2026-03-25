"""OpenAI-compatible chat completions client (sync httpx)."""

import json
import logging
from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


class LLMClient:
    """Minimal client for ``/v1/chat/completions``-style APIs.

    Reads model and base URL from settings and parses the assistant message content
    as JSON for structured outputs.
    """

    def __init__(self, settings: Settings) -> None:
        self._api_key = (settings.OPENAI_API_KEY or "").strip()
        self._base_url = settings.OPENAI_BASE_URL.strip().rstrip("/")
        self._model = settings.OPENAI_MODEL.strip()
        self._timeout = float(settings.HTTP_TIMEOUT)

    def chat_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Call chat completions and return the assistant message parsed as a JSON object.

        Uses ``response_format`` with ``type: json_object`` when supported by the server.

        Args:
            system_prompt: System role content.
            user_prompt: User role content.

        Returns:
            Parsed JSON object (Python ``dict``).

        Raises:
            ExternalServiceError: On missing API key, HTTP errors, non-JSON body, or invalid JSON in content.
        """
        if not self._api_key:
            raise ExternalServiceError("OPENAI_API_KEY is missing; cannot call chat completions.")

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx.RequestError as exc:
            logger.warning("LLM request error: %s", exc)
            raise ExternalServiceError(f"LLM request failed: {exc}") from exc

        if response.status_code >= 400:
            body = (response.text or "")[:800]
            logger.warning("LLM HTTP %s: %s", response.status_code, body)
            raise ExternalServiceError(
                f"LLM returned HTTP {response.status_code}. {body}".strip()
            )

        try:
            envelope = response.json()
        except ValueError as exc:
            raise ExternalServiceError("LLM response is not valid JSON.") from exc

        if not isinstance(envelope, dict):
            raise ExternalServiceError("LLM response is not a JSON object.")

        try:
            choices = envelope["choices"]
            content = choices[0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ExternalServiceError("LLM response missing choices/message/content.") from exc

        if content is None or not str(content).strip():
            raise ExternalServiceError("LLM returned empty message content.")

        try:
            parsed = json.loads(str(content))
        except json.JSONDecodeError as exc:
            raise ExternalServiceError("LLM message content is not valid JSON.") from exc

        if not isinstance(parsed, dict):
            raise ExternalServiceError("LLM JSON must be an object at the top level.")

        return parsed
