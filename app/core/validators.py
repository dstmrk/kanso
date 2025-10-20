"""Data validation models using Pydantic.

This module provides Pydantic models for validating data structures read from
Google Sheets. Validation happens before data processing to catch errors early
and provide clear, actionable error messages.

The validation is non-blocking by default: errors are logged as warnings but
don't prevent data loading, allowing the application to handle imperfect data
gracefully.

Key features:
    - Date format validation (YYYY-MM)
    - Monetary field format checking
    - Category and amount validation for expenses
    - Batch validation with detailed error reporting

Example:
    >>> from app.core.validators import DataSheetRow, validate_dataframe_structure
    >>> data = [{'Date': '2024-01', 'Net_Worth': '€ 1.000', 'Income': '€ 3.000'}]
    >>> is_valid, errors = validate_dataframe_structure(data, DataSheetRow)
    >>> is_valid
    True
"""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.constants import DATE_FORMAT_STORAGE

logger = logging.getLogger(__name__)


class DataSheetRow(BaseModel):
    """Validation model for a row in the main Data sheet.

    Validates the structure and format of monthly financial data rows, including:
    - Date in YYYY-MM format (required)
    - Monetary fields (Net Worth, Income, Expenses, asset categories, etc.)

    All monetary fields are optional except Date. Monetary values can be in various
    formats (€ 1.234,56, $1,234.56, etc.) and are validated for parsability.

    Attributes:
        Date: Month in YYYY-MM format (e.g., "2024-01")
        Net_Worth: Optional net worth value with currency symbol
        Income: Optional monthly income with currency symbol
        Expenses: Optional monthly expenses with currency symbol
        Cash: Optional cash holdings
        Pension_Fund: Optional pension fund value
        Stocks: Optional stock portfolio value
        Real_Estate: Optional real estate value
        Crypto: Optional cryptocurrency holdings
        Other: Optional other assets
        Mortgage: Optional mortgage debt
        Loans: Optional loan debt

    Example:
        >>> row = DataSheetRow(
        ...     Date='2024-01',
        ...     Net_Worth='€ 10.000',
        ...     Income='€ 3.000',
        ...     Expenses='€ 2.000'
        ... )
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="allow")

    Date: str
    Net_Worth: str | None = None
    Income: str | None = None
    Expenses: str | None = None
    Cash: str | None = None
    Pension_Fund: str | None = None
    Stocks: str | None = None
    Real_Estate: str | None = None
    Crypto: str | None = None
    Other: str | None = None
    Mortgage: str | None = None
    Loans: str | None = None

    @field_validator("Date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate that Date is in YYYY-MM format.

        Args:
            v: Date string to validate

        Returns:
            Stripped date string if valid

        Raises:
            ValueError: If date is empty or not in YYYY-MM format
        """
        if not v:
            raise ValueError("Date cannot be empty")

        try:
            # Try to parse date with expected format
            datetime.strptime(v.strip(), DATE_FORMAT_STORAGE)
            return v.strip()
        except ValueError as e:
            raise ValueError(f"Date must be in YYYY-MM format, got: {v}") from e

    @field_validator(
        "Net_Worth",
        "Income",
        "Expenses",
        "Cash",
        "Pension_Fund",
        "Stocks",
        "Real_Estate",
        "Crypto",
        "Other",
        "Mortgage",
        "Loans",
    )
    @classmethod
    def validate_monetary_field(cls, v: str | None) -> str | None:
        """Validate that monetary fields contain parsable numeric values.

        Allows various currency formats:
        - European: "€ 1.234,56"
        - US/UK: "$1,234.56", "£1,234.56"
        - Swiss: "Fr 1.234,56"
        - Japanese: "¥1,234"
        - Plain: "1234.56"

        Args:
            v: Monetary value string to validate, or None

        Returns:
            Original string if valid, None if empty or None

        Note:
            Logs a warning if the field contains no digits but doesn't raise an error,
            allowing the application to handle invalid values gracefully.
        """
        if v is None or v.strip() == "":
            return None

        # Remove common currency symbols and spaces
        cleaned = v.replace("€", "").replace("$", "").replace(" ", "")

        # Check if it's a valid monetary value (numbers, dots, commas)
        if not any(c.isdigit() for c in cleaned):
            logger.warning(f"Monetary field contains no digits: {v}")
            return None

        return v


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

    Date: str
    Merchant: str
    Amount: str
    Category: str
    Type: str

    @field_validator("Date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate that Date is in YYYY-MM format.

        Args:
            v: Date string to validate

        Returns:
            Stripped date string if valid

        Raises:
            ValueError: If date is empty or not in YYYY-MM format
        """
        if not v:
            raise ValueError("Date cannot be empty")

        try:
            datetime.strptime(v.strip(), DATE_FORMAT_STORAGE)
            return v.strip()
        except ValueError as e:
            raise ValueError(f"Date must be in YYYY-MM format, got: {v}") from e

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


def validate_dataframe_structure(
    data: list[dict[str, Any]], model: type[BaseModel]
) -> tuple[bool, list[str]]:
    """Validate a list of dictionaries (DataFrame rows) against a Pydantic model.

    Performs batch validation on all rows and collects error messages.
    Logs only the first 10 errors to avoid log spam.

    Args:
        data: List of dictionaries representing DataFrame rows
        model: Pydantic model class to validate against (DataSheetRow or ExpenseRow)

    Returns:
        Tuple containing:
        - is_valid (bool): True if all rows are valid, False otherwise
        - error_messages (list[str]): List of error messages for invalid rows

    Example:
        >>> data = [
        ...     {'Date': '2024-01', 'Net_Worth': '€ 10.000'},
        ...     {'Date': 'invalid', 'Net_Worth': '€ 11.000'}
        ... ]
        >>> is_valid, errors = validate_dataframe_structure(data, DataSheetRow)
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
