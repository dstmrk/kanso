"""Data validation models using Pydantic.

This module provides Pydantic models for validating data structures read from
Google Sheets. Validation happens before data processing to catch errors early
and provide clear, actionable error messages.

The validation is non-blocking by default: errors are logged as warnings but
don't prevent data loading, allowing the application to handle imperfect data
gracefully.

Key features:
    - Date format validation (YYYY-MM) for all sheet types
    - Monetary field format checking for all values
    - Category and amount validation for expenses
    - Multi-index column support for assets, liabilities, and incomes
    - Batch validation with detailed error reporting

Available models:
    - ExpenseRow: Validates expense transactions (Date, Merchant, Amount, Category, Type)
    - AssetRow: Validates asset data with multi-index columns (Date + dynamic columns)
    - LiabilityRow: Validates liability data with multi-index columns (Date + dynamic columns)
    - IncomeRow: Validates income data with multi-index columns (Date + dynamic columns)

Example:
    >>> from app.core.validators import ExpenseRow, AssetRow, validate_dataframe_structure
    >>> expense_data = [{'Date': '2024-01', 'Merchant': 'Store', 'Amount': '€ 100', 'Category': 'Food', 'Type': 'Variable'}]
    >>> is_valid, errors = validate_dataframe_structure(expense_data, ExpenseRow)
    >>> is_valid
    True
    >>> asset_data = [{'Date': '2024-01', '("Cash", "Checking")': '1000'}]
    >>> is_valid, errors = validate_dataframe_structure(asset_data, AssetRow)
    >>> is_valid
    True
"""

import json
import logging
import re
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, field_validator, model_validator

from app.core.constants import DATE_FORMAT_STORAGE

logger = logging.getLogger(__name__)


# =============================================================================
# Reusable Field Validators
# =============================================================================


def _validate_date_format(v: str) -> str:
    """Validate that a date string is in YYYY-MM format.

    This is a reusable validator function used by the DateField type annotation.
    It ensures consistent date validation across all sheet types (Expenses, Assets,
    Liabilities, Incomes).

    Args:
        v: Date string to validate

    Returns:
        Stripped date string if valid

    Raises:
        ValueError: If date is empty or not in YYYY-MM format

    Example:
        >>> _validate_date_format("2024-01")
        '2024-01'
        >>> _validate_date_format("  2024-01  ")
        '2024-01'
        >>> _validate_date_format("invalid")
        Traceback (most recent call last):
            ...
        ValueError: Date must be in YYYY-MM format, got: invalid
    """
    if not v:
        raise ValueError("Date cannot be empty")

    try:
        datetime.strptime(v.strip(), DATE_FORMAT_STORAGE)
        return v.strip()
    except ValueError as e:
        raise ValueError(f"Date must be in YYYY-MM format, got: {v}") from e


# Reusable date field type with built-in validation
# Usage: Date: DateField (instead of Date: str with @field_validator)
DateField = Annotated[str, BeforeValidator(_validate_date_format)]


class ExpenseRow(BaseModel):
    """Validation model for a row in the Expenses sheet.

    Validates expense transactions with date, merchant, amount, category, and type.
    All fields are required and must be properly formatted.

    Attributes:
        Date: Expense date in YYYY-MM format (e.g., "2024-01")
        Merchant: Merchant/store name (e.g., "Amazon", "Local Grocery", "Netflix")
        Amount: Expense amount with currency symbol (e.g., "€ 500", "$500")
        Category: Expense category name (e.g., "Food", "Transport", "Housing")
        Type: Expense type (e.g., "Fixed", "Variable", "One-time")

    Example:
        >>> expense = ExpenseRow(
        ...     Date='2024-01',
        ...     Merchant='Amazon',
        ...     Amount='€ 50',
        ...     Category='Shopping',
        ...     Type='Variable'
        ... )
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    Date: DateField
    Merchant: str
    Amount: str
    Category: str
    Type: str

    @field_validator("Category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate that Category is not empty.

        Args:
            v: Category string to validate

        Returns:
            Stripped category string if valid

        Raises:
            ValueError: If category is empty or contains only whitespace
        """
        if not v or not v.strip():
            raise ValueError("Category cannot be empty")
        return v.strip()

    @field_validator("Merchant")
    @classmethod
    def validate_merchant(cls, v: str) -> str:
        """Validate that Merchant is not empty.

        Args:
            v: Merchant string to validate

        Returns:
            Stripped merchant string if valid

        Raises:
            ValueError: If merchant is empty or contains only whitespace
        """
        if not v or not v.strip():
            raise ValueError("Merchant cannot be empty")
        return v.strip()

    @field_validator("Type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate that Type is not empty.

        Args:
            v: Type string to validate

        Returns:
            Stripped type string if valid

        Raises:
            ValueError: If type is empty or contains only whitespace
        """
        if not v or not v.strip():
            raise ValueError("Type cannot be empty")
        return v.strip()

    @field_validator("Amount")
    @classmethod
    def validate_amount(cls, v: str) -> str:
        """Validate that Amount can be parsed as a monetary value.

        Allows various currency formats: "€ 1.234,56", "$1,234.56", "1234.56", etc.

        Args:
            v: Amount string to validate

        Returns:
            Original amount string if valid

        Raises:
            ValueError: If amount is empty or contains no numeric digits
        """
        if not v or not v.strip():
            raise ValueError("Amount cannot be empty")

        # Remove common currency symbols and spaces
        cleaned = v.replace("€", "").replace("$", "").replace(" ", "")

        # Check if it contains at least one digit
        if not any(c.isdigit() for c in cleaned):
            raise ValueError(f"Amount must contain numbers, got: {v}")

        return v


class MonetaryValueValidatorMixin:
    """Mixin for validating monetary values in MultiIndex models.

    Provides common validation logic for models with dynamic monetary columns
    (Assets, Liabilities, Incomes) that use Pydantic's extra fields mechanism.

    This mixin validates that all extra fields contain parse-able monetary values
    or are empty/NaN. It should be mixed into Pydantic models that have a Date
    field plus dynamic monetary columns.
    """

    @model_validator(mode="after")
    def validate_monetary_values(self):
        """Validate that all monetary columns contain parse-able values.

        Checks all extra fields (monetary columns) to ensure they can be parsed
        as numeric values or are empty/NaN. This validator works with Pydantic v2's
        __pydantic_extra__ mechanism for models with extra="allow".

        Returns:
            Self if validation passes

        Raises:
            ValueError: If any monetary value is invalid
        """
        # Check extra fields (Pydantic v2 stores them in __pydantic_extra__)
        if hasattr(self, "__pydantic_extra__") and self.__pydantic_extra__:
            for field_name, value in self.__pydantic_extra__.items():
                # Skip None, empty strings, or common NaN representations
                if value is None or value == "" or str(value).lower() in ["nan", "n/a"]:
                    continue

                # Check if value contains at least one digit
                cleaned = (
                    str(value).replace("€", "").replace("$", "").replace(" ", "").replace(",", "")
                )
                if cleaned and not any(c.isdigit() for c in cleaned):
                    # Get the model class name for error message
                    model_type = self.__class__.__name__.replace("Row", "")
                    raise ValueError(f"{model_type} '{field_name}' has invalid value: {value}")

        return self


class AssetRow(MonetaryValueValidatorMixin, BaseModel):
    """Validation model for a row in the Assets sheet.

    Assets use multi-index columns like (Category, Item), e.g., ('Cash', 'Checking'),
    ('Investments', 'Stocks'). This model validates the Date column and ensures
    monetary values are parse-able.

    Attributes:
        Date: Asset date in YYYY-MM format (e.g., "2024-01")
        **extra_fields: Dynamic asset columns with monetary values

    Example:
        >>> asset = AssetRow(
        ...     Date='2024-01',
        ...     **{'("Cash", "Checking")': '1000', '("Investments", "Stocks")': '5000'}
        ... )
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="allow")

    Date: DateField


class LiabilityRow(MonetaryValueValidatorMixin, BaseModel):
    """Validation model for a row in the Liabilities sheet.

    Liabilities use multi-index columns like (Category, Item), e.g., ('Mortgage', ''),
    ('Loans', 'Car'). This model validates the Date column and ensures
    monetary values are parse-able.

    Attributes:
        Date: Liability date in YYYY-MM format (e.g., "2024-01")
        **extra_fields: Dynamic liability columns with monetary values

    Example:
        >>> liability = LiabilityRow(
        ...     Date='2024-01',
        ...     **{'("Mortgage", "")': '250000', '("Loans", "Car")': '15000'}
        ... )
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="allow")

    Date: DateField


class IncomeRow(MonetaryValueValidatorMixin, BaseModel):
    """Validation model for a row in the Incomes sheet.

    Incomes use multi-index columns like (Source, Item), e.g., ('Salary', ''),
    ('Freelance', 'Project A'). This model validates the Date column and ensures
    monetary values are parse-able.

    Attributes:
        Date: Income date in YYYY-MM format (e.g., "2024-01")
        **extra_fields: Dynamic income columns with monetary values

    Example:
        >>> income = IncomeRow(
        ...     Date='2024-01',
        ...     **{'("Salary", "")': '3000', '("Freelance", "Project A")': '500'}
        ... )
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="allow")

    Date: DateField


def validate_dataframe_structure(
    data: list[dict[str, Any]], model: type[BaseModel]
) -> tuple[bool, list[str]]:
    """Validate a list of dictionaries (DataFrame rows) against a Pydantic model.

    Performs batch validation on all rows and collects error messages.
    Logs only the first 10 errors to avoid log spam.

    Args:
        data: List of dictionaries representing DataFrame rows
        model: Pydantic model class to validate against (e.g., ExpenseRow)

    Returns:
        Tuple containing:
        - is_valid (bool): True if all rows are valid, False otherwise
        - error_messages (list[str]): List of error messages for invalid rows

    Example:
        >>> data = [
        ...     {'Date': '2024-01', 'Merchant': 'Store', 'Amount': '€ 100', 'Category': 'Food', 'Type': 'Variable'},
        ...     {'Date': 'invalid', 'Merchant': 'Store', 'Amount': '€ 100', 'Category': 'Food', 'Type': 'Variable'}
        ... ]
        >>> is_valid, errors = validate_dataframe_structure(data, ExpenseRow)
        >>> is_valid
        False
        >>> len(errors)
        1
    """
    errors = []

    for i, row in enumerate(data):
        try:
            model.model_validate(row)
        except Exception as e:
            errors.append(f"Row {i + 1}: {str(e)}")
            # Only log first 10 errors to avoid spam
            if len(errors) <= 10:
                logger.warning(f"Validation error in row {i + 1}: {e}")

    is_valid = len(errors) == 0

    if not is_valid:
        logger.error(f"Validation failed with {len(errors)} error(s)")

    return is_valid, errors


# =============================================================================
# Google Sheets Setup Validation
# =============================================================================
# The following functions validate user input for Google Sheets configuration
# during onboarding and in settings. They are used by both onboarding.py and
# settings.py to avoid code duplication.


def clean_google_sheets_url(url: str) -> str:
    """Extract clean Google Sheets URL with only the workbook ID.

    Removes query parameters, fragments, and trailing paths that users often
    copy accidentally (e.g., ?gid=123#gid=456, /edit?usp=sharing).

    Args:
        url: Raw Google Sheets URL (possibly with extra parameters)

    Returns:
        Cleaned URL in format: https://docs.google.com/spreadsheets/d/{ID}/edit

    Raises:
        ValueError: If URL doesn't contain a valid workbook ID

    Examples:
        >>> clean_google_sheets_url("https://docs.google.com/spreadsheets/d/ABC123/edit?gid=0#gid=0")
        'https://docs.google.com/spreadsheets/d/ABC123/edit'
        >>> clean_google_sheets_url("https://docs.google.com/spreadsheets/d/ABC123/edit?usp=sharing")
        'https://docs.google.com/spreadsheets/d/ABC123/edit'
    """
    # Extract workbook ID using regex
    # Pattern: /d/{WORKBOOK_ID}/
    pattern = r"https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)"
    match = re.search(pattern, url)

    if not match:
        raise ValueError(
            "Could not extract workbook ID from URL. "
            "Expected format: https://docs.google.com/spreadsheets/d/WORKBOOK_ID/..."
        )

    workbook_id = match.group(1)

    # Reconstruct clean URL
    return f"https://docs.google.com/spreadsheets/d/{workbook_id}/edit"


def validate_google_sheets_url(url: str | None) -> tuple[bool, str]:
    """Validate Google Sheets URL format.

    Args:
        url: URL string to validate

    Returns:
        Tuple of (is_valid, error_message)
        - If valid: (True, "")
        - If invalid: (False, "Error message explaining why")

    Examples:
        >>> validate_google_sheets_url("https://docs.google.com/spreadsheets/d/ABC123/edit")
        (True, '')
        >>> validate_google_sheets_url("https://example.com")
        (False, 'Invalid Google Sheets URL format')
    """
    if not url or not isinstance(url, str):
        return (False, "URL is required")

    if not url.startswith("https://docs.google.com/spreadsheets/"):
        return (False, "Invalid Google Sheets URL format")

    # Try to extract workbook ID
    pattern = r"https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)"
    if not re.search(pattern, url):
        return (
            False,
            "Could not find workbook ID in URL. Expected format: "
            "https://docs.google.com/spreadsheets/d/WORKBOOK_ID/...",
        )

    return (True, "")


def validate_google_credentials_json(
    credentials_json: str | None,
) -> tuple[Literal[True], dict] | tuple[Literal[False], str]:
    """Validate Google Service Account credentials JSON.

    Args:
        credentials_json: Raw JSON string containing service account credentials

    Returns:
        - If valid: (True, parsed_json_dict)
        - If invalid: (False, error_message)

    Examples:
        >>> valid_json = '{"type": "service_account", "project_id": "test"}'
        >>> validate_google_credentials_json(valid_json)
        (True, {'type': 'service_account', 'project_id': 'test'})
        >>> validate_google_credentials_json("invalid json")
        (False, 'Invalid JSON format: ...')
    """
    if not credentials_json or not isinstance(credentials_json, str):
        return (False, "Credentials JSON is required")

    # Try to parse JSON
    try:
        json_data = json.loads(credentials_json)
    except json.JSONDecodeError as e:
        return (False, f"Invalid JSON format: {str(e)}")

    # Check if it's a dict
    if not isinstance(json_data, dict):
        return (False, "Credentials JSON must be an object (not array or primitive)")

    # Validate it looks like a service account credential
    if "type" not in json_data:
        return (False, "Missing 'type' field in credentials JSON")

    if json_data.get("type") != "service_account":
        return (
            False,
            f"Invalid credential type: '{json_data.get('type')}'. Expected 'service_account'",
        )

    # Check for other required fields (basic check)
    required_fields = ["project_id", "private_key_id", "private_key", "client_email"]
    missing_fields = [field for field in required_fields if field not in json_data]

    if missing_fields:
        return (
            False,
            f"Missing required fields in service account JSON: {', '.join(missing_fields)}",
        )

    # All good
    return (True, json_data)


def validate_credentials_and_url(
    credentials_content: str, url: str
) -> tuple[Literal[True], dict, str] | tuple[Literal[False], str, None]:
    """Validate Google credentials JSON and Sheet URL together.

    Returns:
        - If valid: (True, parsed_json_dict, cleaned_url)
        - If invalid: (False, error_message, None)
    """
    is_valid_creds, creds_result = validate_google_credentials_json(credentials_content)
    if not is_valid_creds:
        return (False, creds_result, None)

    is_valid_url, url_error = validate_google_sheets_url(url)
    if not is_valid_url:
        return (False, url_error, None)

    try:
        cleaned = clean_google_sheets_url(url)
    except ValueError as e:
        return (False, str(e), None)

    return (True, creds_result, cleaned)
