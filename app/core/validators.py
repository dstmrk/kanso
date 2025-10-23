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
    >>> from app.core.validators import ExpenseRow, validate_dataframe_structure
    >>> data = [{'Date': '2024-01', 'Merchant': 'Store', 'Amount': '€ 100', 'Category': 'Food', 'Type': 'Variable'}]
    >>> is_valid, errors = validate_dataframe_structure(data, ExpenseRow)
    >>> is_valid
    True
"""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.constants import DATE_FORMAT_STORAGE

logger = logging.getLogger(__name__)


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
