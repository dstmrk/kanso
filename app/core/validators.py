"""
Data validation models using Pydantic.

These models validate the structure of data read from Google Sheets
before processing, catching errors early and providing clear error messages.
"""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.constants import DATE_FORMAT_STORAGE

logger = logging.getLogger(__name__)


class DataSheetRow(BaseModel):
    """
    Validation model for a row in the main Data sheet.

    Validates Date format and ensures required monetary fields are present.
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
        """Validate that Date is in YYYY-MM format."""
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
        """
        Validate monetary fields can be parsed.

        Allows various formats: "€ 1.234,56", "1234.56", "1,234.56", etc.
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
    """
    Validation model for a row in the Expenses sheet.

    Validates Month format, Category presence, and Amount format.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    Month: str
    Category: str
    Amount: str

    @field_validator("Month")
    @classmethod
    def validate_month_format(cls, v: str) -> str:
        """Validate that Month is in YYYY-MM format."""
        if not v:
            raise ValueError("Month cannot be empty")

        try:
            datetime.strptime(v.strip(), DATE_FORMAT_STORAGE)
            return v.strip()
        except ValueError as e:
            raise ValueError(f"Month must be in YYYY-MM format, got: {v}") from e

    @field_validator("Category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate that Category is not empty."""
        if not v or not v.strip():
            raise ValueError("Category cannot be empty")
        return v.strip()

    @field_validator("Amount")
    @classmethod
    def validate_amount(cls, v: str) -> str:
        """
        Validate that Amount can be parsed as a monetary value.

        Allows various formats: "€ 1.234,56", "1234.56", etc.
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
    """
    Validate a list of dictionaries (DataFrame rows) against a Pydantic model.

    Args:
        data: List of dictionaries representing DataFrame rows
        model: Pydantic model class to validate against

    Returns:
        Tuple of (is_valid, error_messages)
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
