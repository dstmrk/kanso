"""Utility functions for services.

This module provides utility functions for common operations including:
- Dictionary caching helpers
- User agent detection
- JSON/DataFrame conversion with MultiIndex support
- Currency and locale handling
- Number formatting for different currencies

Example:
    >>> from app.services.utils import format_currency, get_user_currency
    >>> currency = get_user_currency()  # Auto-detect from locale
    >>> formatted = format_currency(1234.56, currency)  # "€1.234" or "$1,235"
"""

import locale
from collections.abc import Callable
from io import StringIO
from typing import Any, Literal

import pandas as pd
from user_agents import parse

from app.core.currency_formats import get_currency_format, get_supported_currencies


def get_or_store(dict: dict[str, Any], key: str, compute_fn: Callable[[], Any]) -> Any:
    """Get value from dict or compute and store it if not present.

    Simple caching helper that checks if a key exists in a dictionary,
    and if not, computes the value and stores it before returning.

    Args:
        dict: Dictionary to check/store in
        key: Key to lookup or store
        compute_fn: Function to call if key is not present (should be cheap to call)

    Returns:
        Value from dict or newly computed value

    Example:
        >>> cache = {}
        >>> value = get_or_store(cache, 'result', lambda: expensive_calculation())
        >>> # Second call returns cached value
        >>> value = get_or_store(cache, 'result', lambda: expensive_calculation())
    """
    if key not in dict:
        dict[key] = compute_fn()
    return dict[key]


def get_user_agent(http_agent: str | None) -> Literal["mobile", "desktop"]:
    """Detect if user agent is mobile or desktop.

    Args:
        http_agent: HTTP User-Agent header string, or None

    Returns:
        "mobile" if user agent indicates mobile device, "desktop" otherwise

    Example:
        >>> get_user_agent("Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)")
        'mobile'
        >>> get_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        'desktop'
    """
    return "mobile" if http_agent and parse(http_agent).is_mobile else "desktop"


def read_json(data: str) -> pd.DataFrame:
    """Read JSON string into DataFrame, handling MultiIndex columns.

    Reconstructs MultiIndex columns from tuples if present in the JSON data.
    This is needed because pandas MultiIndex columns are serialized as tuples
    when using orient="split".

    Args:
        data: JSON string in split-oriented format

    Returns:
        DataFrame with proper column structure (single or MultiIndex)

    Example:
        >>> json_str = df.to_json(orient='split')
        >>> restored_df = read_json(json_str)
    """
    df = pd.read_json(StringIO(data), orient="split")

    # Check if columns are tuples (indicates MultiIndex was serialized)
    if df.columns.size > 0 and isinstance(df.columns[0], tuple):
        # Reconstruct MultiIndex from tuples
        df.columns = pd.MultiIndex.from_tuples(df.columns)

    return df


def get_user_currency() -> str:
    """Get currency code from user locale with fallback to USD.

    Attempts to detect currency from system locale. Only returns currency if
    it's one of the main supported currencies: EUR, USD, GBP, CHF, JPY.
    Otherwise returns USD as safe default.

    Returns:
        Currency code string (one of: EUR, USD, GBP, CHF, JPY)

    Example:
        >>> # On system with EUR locale
        >>> get_user_currency()
        'EUR'
        >>> # On system with unsupported currency or no locale
        >>> get_user_currency()
        'USD'
    """
    supported_currencies = set(get_supported_currencies())

    try:
        conv = locale.localeconv()
        # Extract currency from locale (format: 'EUR ' or 'USD ')
        currency_raw = conv.get("int_curr_symbol", "USD")
        currency = str(currency_raw).strip() if currency_raw else "USD"

        # Return currency if supported, otherwise default to USD
        return currency if currency in supported_currencies else "USD"
    except Exception:
        return "USD"


def format_percentage(value: float, currency: str = "USD") -> str:
    """Format percentage with correct decimal separator based on currency.

    Uses comma as decimal separator for EUR/CHF (European style), dot for others.

    Args:
        value: The percentage value as decimal (e.g., 0.1234 for 12.34%)
        currency: Currency code to determine decimal separator (EUR, USD, GBP, CHF, JPY)

    Returns:
        Formatted percentage string with % symbol

    Example:
        >>> format_percentage(0.1234, "EUR")
        '12,34%'
        >>> format_percentage(0.1234, "USD")
        '12.34%'
    """
    # Calculate percentage
    percentage = value * 100

    # Get decimal separator from centralized config
    fmt = get_currency_format(currency)

    # Format with decimal separator from currency config
    # If decimal_sep is comma, replace dot with comma
    if fmt.decimal_sep == ",":
        return f"{percentage:.2f}%".replace(".", ",")
    else:
        return f"{percentage:.2f}%"


def format_currency(amount: float, currency: str | None = None) -> str:
    """Format amount as currency with specified currency code.

    Formats numbers according to currency conventions:
    - EUR, CHF: Dot for thousands, symbol after (1.234 €)
    - USD, GBP, JPY: Comma for thousands, symbol before ($ 1,234)
    - All currencies have space between symbol and number

    Args:
        amount: The monetary amount to format (will be rounded to integer)
        currency: Currency code (EUR, USD, GBP, CHF, JPY). If None, uses user locale.

    Returns:
        Formatted currency string with symbol and space (e.g., "1.235 €", "$ 1,235")

    Example:
        >>> format_currency(1234.56, "EUR")
        '1.235 €'
        >>> format_currency(1234.56, "USD")
        '$ 1,235'
        >>> format_currency(1234.56, "GBP")
        '£ 1,235'
        >>> format_currency(1234.56, "JPY")
        '¥ 1,235'
    """
    if currency is None:
        # Fallback to locale-based formatting
        try:
            return locale.currency(amount, grouping=True)
        except Exception:
            currency = "USD"

    # Get currency format from centralized config
    fmt = get_currency_format(currency)

    # Format with appropriate thousands separator
    # Python's format always uses comma, so replace if needed
    formatted = f"{amount:,.0f}"
    if fmt.thousands_sep == ".":
        formatted = formatted.replace(",", ".")

    # Position symbol based on currency convention (with space)
    if fmt.position == "before":
        return f"{fmt.symbol} {formatted}"
    else:
        return f"{formatted} {fmt.symbol}"
