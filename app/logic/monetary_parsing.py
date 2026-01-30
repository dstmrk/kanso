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


def _coerce_non_string(value: Any) -> float:
    """Convert non-string value to float, treating None and NaN as 0.0."""
    if value is None:
        return 0.0
    result = float(value)
    return 0.0 if math.isnan(result) else result


def _resolve_currency_format(currency: str | None, value: str) -> tuple[str | None, str, str]:
    """Detect currency and return (detected_currency, thousand_sep, decimal_sep)."""
    detected = currency or detect_currency(value)
    if detected and detected in CURRENCY_FORMATS:
        fmt = get_currency_format(detected)
    else:
        fmt = get_currency_format("EUR")
    return detected, fmt.thousands_sep, fmt.decimal_sep


def _strip_currency_symbols(value: str) -> str:
    """Remove currency symbols, codes, and whitespace from a monetary string."""
    cleaned = re.sub(r"[€$£¥]|Fr|CHF|JPY|USD|EUR|GBP", "", value).strip()
    return cleaned.replace(" ", "")


def _try_parse_plain_number(cleaned: str) -> float | None:
    """Attempt to parse a plain number (no currency detected).

    Returns the parsed float if the format is unambiguous, or None to signal
    that currency-specific parsing should be used instead.
    """
    dot_count = cleaned.count(".")
    comma_count = cleaned.count(",")

    if dot_count == 1 and comma_count == 0:
        return float(cleaned)
    if comma_count == 1 and dot_count == 0:
        return float(cleaned.replace(",", "."))
    if dot_count == 0 and comma_count == 0:
        return float(cleaned) if cleaned else 0.0
    # Multiple separators — needs currency-specific logic
    return None


def _parse_with_separators(cleaned: str, thousand_sep: str, decimal_sep: str) -> float:
    """Parse a cleaned numeric string using explicit thousand/decimal separators."""
    if thousand_sep not in cleaned and (not decimal_sep or decimal_sep not in cleaned):
        return float(cleaned) if cleaned else 0.0

    if thousand_sep:
        cleaned = cleaned.replace(thousand_sep, "")
    if decimal_sep and decimal_sep != ".":
        cleaned = cleaned.replace(decimal_sep, ".")

    return float(cleaned) if cleaned else 0.0


def _log_parse_error(value: str, cleaned: str, error: Exception) -> None:
    """Log a parse failure, distinguishing text labels from real data errors."""
    if cleaned and cleaned.replace("_", "").replace(" ", "").isalpha():
        logger.debug(
            f"Skipping text value '{value}' during monetary parsing (likely a header/label)"
        )
    else:
        logger.error(
            f"Failed to parse monetary value '{value}' (cleaned: '{cleaned}'): {error}. "
            "This indicates a data quality issue in the source sheet."
        )


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
        return _coerce_non_string(value)

    detected_currency, thousand_sep, decimal_sep = _resolve_currency_format(currency, value)
    cleaned = _strip_currency_symbols(value)

    if not cleaned or cleaned == "-":
        return 0.0

    try:
        if detected_currency is None:
            result = _try_parse_plain_number(cleaned)
            if result is not None:
                return result

        return _parse_with_separators(cleaned, thousand_sep, decimal_sep)

    except (ValueError, TypeError) as e:
        _log_parse_error(value, cleaned, e)
        return 0.0
