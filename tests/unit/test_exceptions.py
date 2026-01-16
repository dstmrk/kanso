"""Tests for the custom exception hierarchy."""

import pytest

from app.core.exceptions import (
    ConfigurationError,
    DataError,
    ExternalServiceError,
    KansoError,
    ValidationError,
)


class TestKansoError:
    """Tests for the base KansoError class."""

    def test_basic_initialization(self) -> None:
        """Test basic error initialization with message only."""
        error = KansoError("Something went wrong")

        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.user_message == KansoError.default_user_message
        assert error.details == {}

    def test_custom_user_message(self) -> None:
        """Test error with custom user message."""
        error = KansoError(
            "Technical error details",
            user_message="Please try again later.",
        )

        assert error.message == "Technical error details"
        assert error.user_message == "Please try again later."

    def test_with_details(self) -> None:
        """Test error with additional details."""
        error = KansoError(
            "Error occurred",
            details={"sheet": "Expenses", "row": 42},
        )

        assert error.details == {"sheet": "Expenses", "row": 42}

    def test_is_exception(self) -> None:
        """Test that KansoError is a proper exception."""
        with pytest.raises(KansoError):
            raise KansoError("Test error")


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_inheritance(self) -> None:
        """Test that ConfigurationError inherits from KansoError."""
        error = ConfigurationError("Missing credentials")

        assert isinstance(error, KansoError)
        assert isinstance(error, Exception)

    def test_default_user_message(self) -> None:
        """Test default user message for configuration errors."""
        error = ConfigurationError("Missing GOOGLE_CREDENTIALS_JSON")

        assert "settings" in error.user_message.lower()


class TestDataError:
    """Tests for DataError."""

    def test_inheritance(self) -> None:
        """Test that DataError inherits from KansoError."""
        error = DataError("Invalid date format")

        assert isinstance(error, KansoError)

    def test_default_user_message(self) -> None:
        """Test default user message for data errors."""
        error = DataError("Could not parse amount")

        assert "spreadsheet" in error.user_message.lower()


class TestExternalServiceError:
    """Tests for ExternalServiceError."""

    def test_inheritance(self) -> None:
        """Test that ExternalServiceError inherits from KansoError."""
        error = ExternalServiceError("API timeout")

        assert isinstance(error, KansoError)

    def test_retryable_default(self) -> None:
        """Test that errors are retryable by default."""
        error = ExternalServiceError("Network timeout")

        assert error.is_retryable is True

    def test_non_retryable(self) -> None:
        """Test non-retryable error flag."""
        error = ExternalServiceError(
            "Invalid API key",
            is_retryable=False,
        )

        assert error.is_retryable is False


class TestValidationError:
    """Tests for ValidationError."""

    def test_inheritance(self) -> None:
        """Test that ValidationError inherits from KansoError."""
        error = ValidationError("Amount must be positive")

        assert isinstance(error, KansoError)

    def test_field_attribute(self) -> None:
        """Test field attribute for form validation."""
        error = ValidationError(
            "Amount must be positive",
            field="amount",
        )

        assert error.field == "amount"

    def test_field_none_by_default(self) -> None:
        """Test field is None when not specified."""
        error = ValidationError("Invalid input")

        assert error.field is None


class TestExceptionCatching:
    """Test exception hierarchy for proper catching."""

    def test_catch_all_with_base_class(self) -> None:
        """Test that all custom exceptions can be caught with KansoError."""
        exceptions = [
            ConfigurationError("config"),
            DataError("data"),
            ExternalServiceError("external"),
            ValidationError("validation"),
        ]

        for exc in exceptions:
            try:
                raise exc
            except KansoError as e:
                assert e is exc  # Same instance

    def test_specific_catching(self) -> None:
        """Test that specific exceptions can be caught separately."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Missing config")

        with pytest.raises(DataError):
            raise DataError("Bad data")

        with pytest.raises(ExternalServiceError):
            raise ExternalServiceError("API failed")

        with pytest.raises(ValidationError):
            raise ValidationError("Invalid input")
