"""Common UI utilities and helpers."""

from typing import Literal, NamedTuple

from nicegui import app

from app.core.currency_formats import get_currency_format, get_locale_for_currency
from app.services import utils


class UserPreferences(NamedTuple):
    """User UI preferences for rendering charts and components.

    Attributes:
        user_agent: Device type (mobile or desktop) for responsive rendering
        currency: User's preferred currency code (USD, EUR, GBP, etc.)
        echart_theme: URL/path to ECharts theme configuration
    """

    user_agent: Literal["mobile", "desktop"]
    currency: str
    echart_theme: str


def get_user_preferences() -> UserPreferences:
    """Get user UI preferences from storage.

    Consolidates all user preference retrieval in one place to avoid
    code duplication across UI components.

    Returns:
        UserPreferences with user_agent, currency, and echart_theme.

    Example:
        >>> prefs = get_user_preferences()
        >>> options = create_chart_options(data, prefs.user_agent, prefs.currency)
        >>> ui.echart(options=options, theme=prefs.echart_theme)
    """
    # Get user agent (mobile vs desktop)
    user_agent_raw = app.storage.client.get("user_agent")
    user_agent: Literal["mobile", "desktop"] = "mobile" if user_agent_raw == "mobile" else "desktop"

    # Get user currency preference (from general storage - shared across devices)
    user_currency = app.storage.general.get("currency", utils.get_user_currency())

    # Get ECharts theme
    echart_theme = app.storage.general.get("echarts_theme_url") or ""

    return UserPreferences(
        user_agent=user_agent,
        currency=user_currency,
        echart_theme=echart_theme,
    )


def get_aggrid_currency_formatter(currency: str) -> str:
    """Generate AG Grid valueFormatter JavaScript for user's currency.

    Creates a JavaScript string for AG Grid's valueFormatter that formats
    monetary values according to the user's currency preferences, including
    proper locale, decimals, and symbol placement.

    Args:
        currency: Currency code (EUR, USD, GBP, etc.).

    Returns:
        JavaScript valueFormatter string for AG Grid columnDefs.

    Example:
        >>> formatter = get_aggrid_currency_formatter("EUR")
        >>> "de-DE" in formatter
        True
        >>> "€" in formatter
        True
        >>> formatter = get_aggrid_currency_formatter("USD")
        >>> "en-US" in formatter
        True
        >>> "$" in formatter
        True
    """
    # Get currency configuration
    fmt = get_currency_format(currency)
    locale = get_locale_for_currency(currency)

    # Build formatter based on decimal support
    if fmt.has_decimals:
        # Standard format with 2 decimals
        number_format = (
            f"value.toLocaleString('{locale}', "
            "{minimumFractionDigits: 2, maximumFractionDigits: 2})"
        )
        null_value = f"'0{fmt.decimal_sep}00'"
    else:
        # No decimals (e.g., JPY)
        number_format = f"value.toLocaleString('{locale}', {{maximumFractionDigits: 0}})"
        null_value = "'0'"

    # Build final formatter with symbol placement
    if fmt.position == "before":
        # Symbol before number: $ 1,234.56
        return f"value != null ? '{fmt.symbol} ' + {number_format} : '{fmt.symbol} ' + {null_value}"
    else:
        # Symbol after number: 1.234,56 €
        return f"value != null ? {number_format} + ' {fmt.symbol}' : {null_value} + ' {fmt.symbol}'"
