"""Monetary value parsing with multi-currency support.

This module provides intelligent parsing of monetary values in various currency formats.
It handles European (1.234,56), US/UK (1,234.56), and Japanese (1,234) formats with
automatic currency detection.

Key features:
    - Automatic currency detection from symbols (€, $, £, ¥, Fr)
    - Support for 5 major currencies (EUR, USD, GBP, CHF, JPY)
    - Intelligent format detection for plain numbers
    - Robust error handling with logging

Example:
    >>> from app.logic.monetary_parsing import parse_monetary_value
    >>> parse_monetary_value("€ 1.234,56")
    1234.56
    >>> parse_monetary_value("$1,234.56")
    1234.56
"""

import logging
import math
import re
from typing import Any

from app.core.currency_formats import CURRENCY_FORMATS, get_currency_format

logger = logging.getLogger(__name__)


def detect_currency(value: str) -> str | None:
    """Detect currency from symbol in string.

    Args:
        value: String potentially containing currency symbol

    Returns:
        Currency code (EUR, USD, GBP, CHF, JPY) or None if not detected
    """
    # Check for each currency symbol from centralized config
    for currency_code, fmt in CURRENCY_FORMATS.items():
        if fmt.symbol in value:
            return currency_code
    # Also check for currency code strings
    if "CHF" in value:
        return "CHF"
    if "JPY" in value:
        return "JPY"
    return None


def parse_monetary_value(value: Any, currency: str | None = None) -> float:
    """Parse monetary value with intelligent currency detection.

    Supports multiple currency formats:
    - EUR, CHF: European format (1.234,56)
    - USD, GBP: US/UK format (1,234.56)
    - JPY: No decimals (1,234)

    Args:
        value: Monetary value as string, int, or float
        currency: Optional currency override (EUR, USD, GBP, CHF, JPY)

    Returns:
        Parsed float value. Returns 0.0 for None, empty strings, or unparseable values.

    Examples:
        >>> parse_monetary_value("€ 1.234,56")
        1234.56
        >>> parse_monetary_value("$1,234.56")
        1234.56
        >>> parse_monetary_value("¥1,234")
        1234.0
        >>> parse_monetary_value("1234.56", currency="EUR")
        123456.0  # Interprets as European: dot = thousand separator
    """
    if not isinstance(value, str):
        if value is None:
            return 0.0
        result = float(value)
        return 0.0 if math.isnan(result) else result

    # Detect or use provided currency
    detected_currency = currency or detect_currency(value)

    # Get format config (default to EUR if not found)
    if detected_currency and detected_currency in CURRENCY_FORMATS:
        fmt = get_currency_format(detected_currency)
    else:
        # Default to EUR format
        fmt = get_currency_format("EUR")

    thousand_sep = fmt.thousands_sep
    decimal_sep = fmt.decimal_sep

    try:
        # Remove currency symbols and extra spaces
        cleaned = re.sub(r"[€$£¥]|Fr|CHF|JPY|USD|EUR|GBP", "", value).strip()
        cleaned = cleaned.replace(" ", "")

        # Special case: empty or just dash (common in Google Sheets for zero with monetary format)
        if not cleaned or cleaned == "-":
            return 0.0

        # Special case: plain number without currency symbol
        # If no currency was detected, treat dots/commas intelligently:
        # - If only one separator exists, it's likely decimal (most common case)
        # - Format like "1234.56" or "1234,56" should be treated as decimal
        if detected_currency is None:
            # Count separators
            dot_count = cleaned.count(".")
            comma_count = cleaned.count(",")

            # Only one type of separator
            if dot_count == 1 and comma_count == 0:
                # Single dot - likely decimal point (standard notation)
                return float(cleaned)
            elif comma_count == 1 and dot_count == 0:
                # Single comma - likely decimal (European)
                return float(cleaned.replace(",", "."))
            elif dot_count == 0 and comma_count == 0:
                # No separators - plain integer or float
                return float(cleaned) if cleaned else 0.0
            # Multiple separators - fall through to currency-specific logic

        # Handle the case where there are no separators (plain number)
        if thousand_sep not in cleaned and (not decimal_sep or decimal_sep not in cleaned):
            # No separators found - treat as plain number
            return float(cleaned) if cleaned else 0.0

        # Remove thousand separator
        if thousand_sep:
            cleaned = cleaned.replace(thousand_sep, "")

        # Replace decimal separator with dot (Python standard)
        if decimal_sep and decimal_sep != ".":
            cleaned = cleaned.replace(decimal_sep, ".")

        return float(cleaned) if cleaned else 0.0

    except (ValueError, TypeError) as e:
        # Check if this looks like a text header or label (contains only letters/underscores)
        if cleaned and cleaned.replace("_", "").replace(" ", "").isalpha():
            # Silently skip text headers/labels - common in sheets with duplicate header rows
            # or when iterating over all columns including label columns
            logger.debug(
                f"Skipping text value '{value}' during monetary parsing (likely a header/label)"
            )
        else:
            logger.error(
                f"Failed to parse monetary value '{value}' (cleaned: '{cleaned}'): {e}. "
                "This indicates a data quality issue in the source sheet."
            )
        return 0.0
