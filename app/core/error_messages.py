"""Standardized error messages for user-facing notifications.

This module provides consistent, actionable error messages that can be
displayed to users via ui.notify() or other UI components.

Usage:
    from app.core.error_messages import get_user_message, ErrorMessages

    # Using constants directly
    ui.notify(ErrorMessages.MISSING_CREDENTIALS, type="negative")

    # From an exception
    except KansoError as e:
        ui.notify(get_user_message(e), type="negative")
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.exceptions import KansoError


class ErrorMessages:
    """Centralized error message constants for UI notifications."""

    # === Configuration Errors ===
    MISSING_CREDENTIALS = "Please add your Google credentials in Settings."
    MISSING_SHEET_URL = "Please add your Google Sheet URL in Settings."
    MISSING_CURRENCY = "Please select a currency in Settings."
    INVALID_CREDENTIALS = "Invalid credentials. Please check your Google service account JSON."
    INVALID_SHEET_URL = "Invalid Google Sheet URL. Please check the format."
    CONFIG_INCOMPLETE = "Configuration incomplete. Please complete setup in Settings."

    # === Connection Errors ===
    CONNECTION_FAILED = "Could not connect to Google Sheets. Please check your internet."
    CONNECTION_TIMEOUT = "Connection timed out. Please try again."
    API_ERROR = "Google Sheets API error. Please try again later."
    RATE_LIMITED = "Too many requests. Please wait a moment and try again."

    # === Data Errors ===
    SHEET_NOT_FOUND = "Worksheet not found. Please check your spreadsheet has the required sheets."
    INVALID_DATA_FORMAT = "Could not read data. Please check your spreadsheet format."
    EMPTY_SHEET = "No data found in spreadsheet. Please add some entries first."
    PARSE_ERROR = "Could not parse data. Please check date and number formats."

    # === Validation Errors ===
    FIELD_REQUIRED = "This field is required."
    INVALID_AMOUNT = "Please enter a valid amount."
    INVALID_DATE = "Please enter a valid date."
    DUPLICATE_ENTRY = "This entry already exists."

    # === Form-specific Messages ===
    QUICK_ADD_MISSING_MERCHANT = "Please enter a merchant name."
    QUICK_ADD_MISSING_AMOUNT = "Please enter a valid amount."
    QUICK_ADD_MISSING_CATEGORY = "Please select or enter a category."
    QUICK_ADD_MISSING_TYPE = "Please select or enter a type."

    # === Success Messages ===
    EXPENSE_ADDED = "Expense added successfully!"
    SETTINGS_SAVED = "Settings saved successfully!"
    DATA_REFRESHED = "Data refreshed successfully!"
    CONFIG_SAVED_AND_VERIFIED = "Configuration saved and connection verified!"

    # === Generic Fallbacks ===
    GENERIC_ERROR = "An error occurred. Please try again."
    UNKNOWN_ERROR = "An unexpected error occurred. Please check logs for details."


def get_user_message(error: "KansoError") -> str:
    """Extract the user-friendly message from a KansoError.

    Args:
        error: A KansoError or subclass instance.

    Returns:
        The user_message attribute if set, otherwise the default message.
    """
    return error.user_message


def format_field_error(field_name: str, message: str) -> str:
    """Format an error message for a specific form field.

    Args:
        field_name: The name of the field with the error.
        message: The error message to display.

    Returns:
        Formatted error message with field context.
    """
    return f"{field_name}: {message}"
