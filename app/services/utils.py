"""Utility functions for services.

This module provides utility functions for common operations including:
- Dictionary caching helpers
- User agent detection
- JSON/DataFrame conversion with MultiIndex support
- Currency and locale handling
- Number formatting for different currencies
- Timestamp formatting with relative time

Example:
    >>> from app.services.utils import format_currency, get_user_currency
    >>> currency = get_user_currency()  # Auto-detect from locale
    >>> formatted = format_currency(1234.56, currency)  # "€1.234" or "$1,235"
"""

import locale
from collections.abc import Callable
from datetime import UTC, datetime
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
    it's one of the supported currencies (10 total).
    Otherwise returns USD as safe default.

    Returns:
        Currency code string (EUR, USD, GBP, CHF, JPY, CAD, AUD, CNY, INR, BRL)

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


def get_currency_from_browser_locale(browser_locale: str | None) -> str:
    """Map browser locale string to currency code.

    Uses language and region from browser locale (e.g., 'en-US', 'pt-BR') to
    determine the most appropriate currency. Falls back to USD if locale is
    unknown or not mappable to supported currencies.

    Args:
        browser_locale: Browser locale string (e.g., 'en-US', 'pt-BR', 'ja-JP')

    Returns:
        Currency code string (EUR, USD, GBP, CHF, JPY, CAD, AUD, CNY, INR, BRL)

    Example:
        >>> get_currency_from_browser_locale('en-US')
        'USD'
        >>> get_currency_from_browser_locale('pt-BR')
        'BRL'
        >>> get_currency_from_browser_locale('de-DE')
        'EUR'
    """
    if not browser_locale:
        return "USD"

    # Normalize to lowercase for easier matching
    locale_lower = browser_locale.lower()

    # Exact locale matches (region-specific)
    locale_map = {
        # English variants
        "en-us": "USD",
        "en-ca": "CAD",
        "en-gb": "GBP",
        "en-au": "AUD",
        "en-in": "INR",
        # Eurozone countries
        "de-de": "EUR",  # Germany
        "de-at": "EUR",  # Austria
        "fr-fr": "EUR",  # France
        "it-it": "EUR",  # Italy
        "es-es": "EUR",  # Spain
        "nl-nl": "EUR",  # Netherlands
        "pt-pt": "EUR",  # Portugal
        "fi-fi": "EUR",  # Finland
        "ie-ie": "EUR",  # Ireland
        "be-be": "EUR",  # Belgium
        # Swiss locales
        "de-ch": "CHF",
        "fr-ch": "CHF",
        "it-ch": "CHF",
        # Asian currencies
        "ja-jp": "JPY",
        "zh-cn": "CNY",
        "zh-sg": "CNY",  # Singapore Chinese often use CNY
        "hi-in": "INR",
        # Americas
        "pt-br": "BRL",
        "fr-ca": "CAD",
    }

    # Try exact match first
    if locale_lower in locale_map:
        return locale_map[locale_lower]

    # Fallback: match by language code only (before the hyphen)
    language = locale_lower.split("-")[0] if "-" in locale_lower else locale_lower
    language_fallback = {
        "en": "USD",  # English defaults to USD
        "de": "EUR",  # German defaults to EUR (most German speakers in EU)
        "fr": "EUR",  # French defaults to EUR (France is largest French-speaking country in EU)
        "es": "EUR",  # Spanish defaults to EUR (Spain, not Latin America)
        "it": "EUR",  # Italian defaults to EUR
        "nl": "EUR",  # Dutch defaults to EUR
        "pt": "EUR",  # Portuguese defaults to EUR (Portugal, not Brazil)
        "ja": "JPY",  # Japanese
        "zh": "CNY",  # Chinese
        "hi": "INR",  # Hindi
    }

    if language in language_fallback:
        return language_fallback[language]

    # Ultimate fallback
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


def get_current_timestamp() -> str:
    """Get current UTC timestamp as ISO 8601 string.

    Returns:
        ISO 8601 formatted timestamp string (e.g., "2025-10-18T14:30:45Z")

    Example:
        >>> get_current_timestamp()
        '2025-10-18T14:30:45Z'
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_timestamp_relative(timestamp_str: str | None) -> tuple[str, str]:
    """Format timestamp with both absolute and relative time.

    Args:
        timestamp_str: ISO 8601 timestamp string, or None

    Returns:
        Tuple of (formatted_datetime, relative_time)
        - formatted_datetime: Human-readable format "YYYY-MM-DD HH:MM:SS"
        - relative_time: Relative time like "2 hours ago", "just now", etc.

    Example:
        >>> format_timestamp_relative("2025-10-18T14:30:45Z")
        ('2025-10-18 14:30:45', '2 hours ago')
        >>> format_timestamp_relative(None)
        ('Never', '')
    """
    if not timestamp_str:
        return ("Never", "")

    try:
        # Parse ISO 8601 timestamp
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        now = datetime.now(UTC)

        # Calculate time difference
        diff = now - timestamp
        seconds = int(diff.total_seconds())

        # Format absolute time
        formatted = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Calculate relative time
        if seconds < 60:
            relative = "just now"
        elif seconds < 3600:  # Less than 1 hour
            minutes = seconds // 60
            relative = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:  # Less than 1 day
            hours = seconds // 3600
            relative = f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 604800:  # Less than 1 week
            days = seconds // 86400
            relative = f"{days} day{'s' if days != 1 else ''} ago"
        elif seconds < 2592000:  # Less than 30 days
            weeks = seconds // 604800
            relative = f"{weeks} week{'s' if weeks != 1 else ''} ago"
        else:
            months = seconds // 2592000
            relative = f"{months} month{'s' if months != 1 else ''} ago"

        return (formatted, relative)

    except (ValueError, AttributeError):
        return ("Invalid timestamp", "")
