"""Domain and application exceptions (extend as the product grows)."""


class AppError(Exception):
    """Base application error."""


class ExternalServiceError(AppError):
    """Raised when an external API (Brave, LLM, etc.) fails."""


class ConfigurationError(AppError):
    """Raised when required app configuration is missing or invalid."""


class ValidationError(AppError):
    """Raised for business-rule validation beyond Pydantic input validation."""
