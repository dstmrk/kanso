"""Tests for standardized error messages."""

from app.core.error_messages import (
    ErrorMessages,
    format_field_error,
    get_user_message,
)
from app.core.exceptions import (
    ConfigurationError,
    DataError,
    ExternalServiceError,
    KansoError,
    ValidationError,
)


class TestErrorMessages:
    """Tests for ErrorMessages constants."""

    def test_configuration_messages_exist(self) -> None:
        """Test that configuration error messages are defined."""
        assert ErrorMessages.MISSING_CREDENTIALS
        assert ErrorMessages.MISSING_SHEET_URL
        assert ErrorMessages.INVALID_CREDENTIALS
        assert ErrorMessages.CONFIG_INCOMPLETE

    def test_connection_messages_exist(self) -> None:
        """Test that connection error messages are defined."""
        assert ErrorMessages.CONNECTION_FAILED
        assert ErrorMessages.CONNECTION_TIMEOUT
        assert ErrorMessages.API_ERROR

    def test_data_messages_exist(self) -> None:
        """Test that data error messages are defined."""
        assert ErrorMessages.SHEET_NOT_FOUND
        assert ErrorMessages.INVALID_DATA_FORMAT
        assert ErrorMessages.EMPTY_SHEET

    def test_validation_messages_exist(self) -> None:
        """Test that validation error messages are defined."""
        assert ErrorMessages.FIELD_REQUIRED
        assert ErrorMessages.INVALID_AMOUNT
        assert ErrorMessages.INVALID_DATE

    def test_success_messages_exist(self) -> None:
        """Test that success messages are defined."""
        assert ErrorMessages.EXPENSE_ADDED
        assert ErrorMessages.SETTINGS_SAVED
        assert ErrorMessages.DATA_REFRESHED

    def test_messages_are_user_friendly(self) -> None:
        """Test that messages don't contain technical jargon."""
        # Should not contain technical terms
        assert "exception" not in ErrorMessages.GENERIC_ERROR.lower()
        assert "traceback" not in ErrorMessages.UNKNOWN_ERROR.lower()

        # Should be actionable (contain guidance)
        assert "please" in ErrorMessages.MISSING_CREDENTIALS.lower()
        assert "please" in ErrorMessages.CONNECTION_FAILED.lower()


class TestGetUserMessage:
    """Tests for get_user_message function."""

    def test_returns_custom_user_message(self) -> None:
        """Test that custom user_message is returned."""
        error = KansoError(
            "Technical details",
            user_message="Please try again later.",
        )
        assert get_user_message(error) == "Please try again later."

    def test_returns_default_for_kanso_error(self) -> None:
        """Test default message for base KansoError."""
        error = KansoError("Something failed")
        assert get_user_message(error) == KansoError.default_user_message

    def test_returns_default_for_configuration_error(self) -> None:
        """Test default message for ConfigurationError."""
        error = ConfigurationError("Missing env var")
        assert "settings" in get_user_message(error).lower()

    def test_returns_default_for_data_error(self) -> None:
        """Test default message for DataError."""
        error = DataError("Parse failed")
        assert "spreadsheet" in get_user_message(error).lower()

    def test_returns_default_for_external_service_error(self) -> None:
        """Test default message for ExternalServiceError."""
        error = ExternalServiceError("API timeout")
        assert "connect" in get_user_message(error).lower()

    def test_returns_default_for_validation_error(self) -> None:
        """Test default message for ValidationError."""
        error = ValidationError("Invalid input")
        assert "check" in get_user_message(error).lower()


class TestFormatFieldError:
    """Tests for format_field_error function."""

    def test_formats_field_and_message(self) -> None:
        """Test basic field error formatting."""
        result = format_field_error("Amount", "Must be positive")
        assert result == "Amount: Must be positive"

    def test_handles_empty_field_name(self) -> None:
        """Test formatting with empty field name."""
        result = format_field_error("", "Error message")
        assert result == ": Error message"

    def test_preserves_message_content(self) -> None:
        """Test that message content is preserved."""
        message = "Please enter a valid date in YYYY-MM format"
        result = format_field_error("Date", message)
        assert message in result
