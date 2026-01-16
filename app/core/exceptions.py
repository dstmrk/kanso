"""Custom exception hierarchy for the Kanso application.

This module defines domain-specific exceptions to provide:
- Clear error categorization (config vs data vs network)
- User-friendly error messages
- Actionable guidance for error resolution

Exception Hierarchy:
    KansoError (base)
    ├── ConfigurationError  → Missing credentials, invalid settings
    ├── DataError           → Invalid data format, parsing failures
    ├── ExternalServiceError → API failures, network timeouts
    └── ValidationError     → Data quality issues, constraint violations
"""

from typing import Any


class KansoError(Exception):
    """Base exception for all Kanso application errors.

    Attributes:
        message: Technical error message for logging.
        user_message: User-friendly message for UI display.
        details: Additional context for debugging.
    """

    default_user_message = "An unexpected error occurred. Please try again."

    def __init__(
        self,
        message: str,
        user_message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize with technical message and optional user-friendly message."""
        super().__init__(message)
        self.message = message
        self.user_message = user_message or self.default_user_message
        self.details = details or {}

    def __str__(self) -> str:
        """Return the technical error message."""
        return self.message


class ConfigurationError(KansoError):
    """Raised when application configuration is missing or invalid.

    Examples:
        - Missing Google Sheets credentials
        - Invalid spreadsheet URL
        - Missing required environment variables
    """

    default_user_message = "Configuration error. Please check your settings in the Settings page."


class DataError(KansoError):
    """Raised when data format is invalid or parsing fails.

    Examples:
        - Invalid date format in spreadsheet
        - Non-numeric value in amount column
        - Missing required columns
    """

    default_user_message = "Could not read your data. Please check your spreadsheet format."


class ExternalServiceError(KansoError):
    """Raised when external service communication fails.

    Examples:
        - Google Sheets API timeout
        - Network connectivity issues
        - API rate limiting
    """

    default_user_message = (
        "Could not connect to external service. Please check your internet connection."
    )

    def __init__(
        self,
        message: str,
        user_message: str | None = None,
        details: dict[str, Any] | None = None,
        *,
        is_retryable: bool = True,
    ) -> None:
        """Initialize with optional retry flag for transient failures."""
        super().__init__(message, user_message, details)
        self.is_retryable = is_retryable


class ValidationError(KansoError):
    """Raised when data validation fails.

    Examples:
        - Empty required field
        - Value out of expected range
        - Duplicate entry detected
    """

    default_user_message = "Please check your input and try again."

    def __init__(
        self,
        message: str,
        user_message: str | None = None,
        details: dict[str, Any] | None = None,
        *,
        field: str | None = None,
    ) -> None:
        """Initialize with optional field name for form validation errors."""
        super().__init__(message, user_message, details)
        self.field = field
