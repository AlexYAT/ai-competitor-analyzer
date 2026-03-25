"""Domain and application exceptions (extend as the product grows)."""


class AppError(Exception):
    """Base application error."""


class ExternalServiceError(AppError):
    """Raised when an external API (Brave, LLM, etc.) fails."""


class ParsingError(AppError):
    """Raised when Selenium / page extraction fails.

    ``message`` must be short and safe to show to end users (no stack traces).
    ``reason_code`` is used by callers (e.g. report) for structured fallbacks:
    ``timeout``, ``selenium_error``, ``invalid_url``.
    """

    def __init__(self, message: str, *, reason_code: str = "selenium_error") -> None:
        super().__init__(message)
        self.reason_code = reason_code


class ConfigurationError(AppError):
    """Raised when required app configuration is missing or invalid."""


class ValidationError(AppError):
    """Raised for business-rule validation beyond Pydantic input validation."""
