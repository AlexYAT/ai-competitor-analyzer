"""Domain and application exceptions (extend as the product grows)."""


class AppError(Exception):
    """Base application error."""


class ExternalServiceError(AppError):
    """Raised when an external API (Brave, LLM, etc.) fails."""


class ValidationError(AppError):
    """Raised for business-rule validation beyond Pydantic input validation."""
