"""Centralized currency formatting configuration.

This module provides a single source of truth for currency formatting rules,
used by both Python (server-side) and JavaScript (client-side) formatters.

All currency formatting logic across the application should reference this
configuration to ensure consistency.

Example:
    >>> from app.core.currency_formats import CURRENCY_FORMATS
    >>> usd = CURRENCY_FORMATS["USD"]
    >>> print(f"{usd.symbol} - thousands: {usd.thousands_sep}")
    $ - thousands: ,
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class CurrencyFormat:
    """Configuration for a single currency's display format.

    Attributes:
        symbol: Currency symbol (e.g., "$", "€", "£")
        position: Where to place symbol relative to number ("before" or "after")
        thousands_sep: Separator for thousands (e.g., "," or ".")
        decimal_sep: Separator for decimals (e.g., "." or ",")
        has_decimals: Whether currency uses decimal places (False for JPY)

    Example:
        >>> eur = CurrencyFormat("€", "after", ".", ",", True)
        >>> # Formats as: 1.234,56 €
    """

    symbol: str
    position: Literal["before", "after"]
    thousands_sep: str
    decimal_sep: str
    has_decimals: bool


# Single source of truth for all currency formatting
CURRENCY_FORMATS: dict[str, CurrencyFormat] = {
    "EUR": CurrencyFormat(
        symbol="€",
        position="after",
        thousands_sep=".",
        decimal_sep=",",
        has_decimals=True,
    ),
    "USD": CurrencyFormat(
        symbol="$",
        position="before",
        thousands_sep=",",
        decimal_sep=".",
        has_decimals=True,
    ),
    "GBP": CurrencyFormat(
        symbol="£",
        position="before",
        thousands_sep=",",
        decimal_sep=".",
        has_decimals=True,
    ),
    "CHF": CurrencyFormat(
        symbol="Fr",
        position="after",
        thousands_sep=".",
        decimal_sep=",",
        has_decimals=True,
    ),
    "JPY": CurrencyFormat(
        symbol="¥",
        position="before",
        thousands_sep=",",
        decimal_sep="",  # No decimal separator
        has_decimals=False,
    ),
    "CAD": CurrencyFormat(
        symbol="C$",
        position="before",
        thousands_sep=",",
        decimal_sep=".",
        has_decimals=True,
    ),
    "AUD": CurrencyFormat(
        symbol="A$",
        position="before",
        thousands_sep=",",
        decimal_sep=".",
        has_decimals=True,
    ),
    "CNY": CurrencyFormat(
        symbol="¥",
        position="before",
        thousands_sep=",",
        decimal_sep=".",
        has_decimals=True,
    ),
    "INR": CurrencyFormat(
        symbol="₹",
        position="before",
        thousands_sep=",",
        decimal_sep=".",
        has_decimals=True,
    ),
    "BRL": CurrencyFormat(
        symbol="R$",
        position="before",
        thousands_sep=".",
        decimal_sep=",",
        has_decimals=True,
    ),
}


def get_currency_format(currency: str) -> CurrencyFormat:
    """Get currency format configuration.

    Args:
        currency: Currency code (EUR, USD, GBP, CHF, JPY, CAD, AUD, CNY, INR, BRL)

    Returns:
        CurrencyFormat instance for the currency

    Raises:
        KeyError: If currency is not supported

    Example:
        >>> fmt = get_currency_format("USD")
        >>> fmt.symbol
        '$'
    """
    return CURRENCY_FORMATS[currency]


def get_currency_symbol(currency: str) -> str:
    """Get currency symbol for given currency code.

    Args:
        currency: Currency code (EUR, USD, GBP, CHF, JPY, CAD, AUD, CNY, INR, BRL)

    Returns:
        Currency symbol string (€, $, £, Fr, ¥, C$, A$, ₹, R$)

    Example:
        >>> get_currency_symbol("EUR")
        '€'
    """
    return CURRENCY_FORMATS.get(currency, CURRENCY_FORMATS["USD"]).symbol


def get_supported_currencies() -> list[str]:
    """Get list of all supported currency codes.

    Returns:
        List of currency code strings (10 currencies)

    Example:
        >>> get_supported_currencies()
        ['EUR', 'USD', 'GBP', 'CHF', 'JPY', 'CAD', 'AUD', 'CNY', 'INR', 'BRL']
    """
    return list(CURRENCY_FORMATS.keys())


# Mapping of currency codes to locale codes for JavaScript toLocaleString()
CURRENCY_LOCALE_MAP: dict[str, str] = {
    "EUR": "de-DE",  # European format: 1.234,56
    "USD": "en-US",  # American format: 1,234.56
    "GBP": "en-GB",  # British format: 1,234.56
    "CHF": "de-CH",  # Swiss format: 1'234.56 (but we use German for consistency)
    "JPY": "ja-JP",  # Japanese format: 1,234 (no decimals)
    "CAD": "en-CA",  # Canadian format: 1,234.56
    "AUD": "en-AU",  # Australian format: 1,234.56
    "CNY": "zh-CN",  # Chinese format: 1,234.56
    "INR": "en-IN",  # Indian format: 1,23,456.78 (unique grouping)
    "BRL": "pt-BR",  # Brazilian format: 1.234,56
}


def get_locale_for_currency(currency: str) -> str:
    """Get JavaScript locale code for currency formatting.

    Args:
        currency: Currency code (EUR, USD, etc.)

    Returns:
        Locale code for toLocaleString() (e.g., "de-DE", "en-US")

    Example:
        >>> get_locale_for_currency("EUR")
        'de-DE'
        >>> get_locale_for_currency("USD")
        'en-US'
    """
    return CURRENCY_LOCALE_MAP.get(currency, "en-US")
