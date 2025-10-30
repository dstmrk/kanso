"""Common UI utilities and helpers."""

from typing import Literal, NamedTuple

from nicegui import app

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
        UserPreferences with user_agent, currency, and echart_theme

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
