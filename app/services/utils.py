import locale
import pandas as pd
from typing import Dict, Any, Callable, Optional, Literal
from user_agents import parse
from io import StringIO

def get_or_store(dict: Dict[str, Any], key: str, compute_fn: Callable[[], Any]) -> Any:
    """Get value from dict or compute and store it if not present."""
    if key not in dict:
        dict[key] = compute_fn()
    return dict[key]

def get_user_agent(http_agent: Optional[str]) -> Literal["mobile", "desktop"]:
    """Detect if user agent is mobile or desktop."""
    return "mobile" if http_agent and parse(http_agent).is_mobile else "desktop"

def read_json(data: str) -> pd.DataFrame:
    """Read JSON string into DataFrame, handling MultiIndex columns."""
    df = pd.read_json(StringIO(data), orient='split')

    # Check if columns are tuples (indicates MultiIndex was serialized)
    if df.columns.size > 0 and isinstance(df.columns[0], tuple):
        # Reconstruct MultiIndex from tuples
        df.columns = pd.MultiIndex.from_tuples(df.columns)

    return df

def get_user_currency() -> str:
    """Get currency code from user locale with fallback to USD.

    Returns currency code only if it's one of the main supported currencies:
    EUR, USD, GBP, CHF, JPY. Otherwise returns USD as default.
    """
    supported_currencies = {'EUR', 'USD', 'GBP', 'CHF', 'JPY'}

    try:
        conv = locale.localeconv()
        # Extract currency from locale (format: 'EUR ' or 'USD ')
        currency = conv.get('int_curr_symbol', 'USD').strip()

        # Return currency if supported, otherwise default to USD
        return currency if currency in supported_currencies else 'USD'
    except Exception:
        return 'USD'

# Currency symbols mapping
CURRENCY_SYMBOLS = {
    'EUR': '€',
    'USD': '$',
    'GBP': '£',
    'CHF': 'Fr',
    'JPY': '¥'
}

def format_percentage(value: float, currency: str = 'USD') -> str:
    """Format percentage with correct decimal separator based on currency.

    Args:
        value: The percentage value (e.g., 0.1234 for 12.34%)
        currency: Currency code to determine decimal separator

    Returns:
        Formatted percentage string
    """
    # Calculate percentage
    percentage = value * 100

    # EUR, CHF use comma as decimal separator
    if currency in ['EUR', 'CHF']:
        return f'{percentage:.2f}%'.replace('.', ',')
    else:
        # USD, GBP, JPY use dot as decimal separator
        return f'{percentage:.2f}%'

def format_currency(amount: float, currency: Optional[str] = None) -> str:
    """Format amount as currency with specified currency code.

    Args:
        amount: The monetary amount to format
        currency: Currency code (EUR, USD, GBP, CHF, JPY). If None, uses user locale.

    Returns:
        Formatted currency string with symbol
    """
    if currency is None:
        # Fallback to locale-based formatting
        try:
            return locale.currency(amount, grouping=True)
        except Exception:
            currency = 'USD'

    symbol = CURRENCY_SYMBOLS.get(currency, '$')

    # Define thousands separator based on currency
    # USD, GBP: comma for thousands (100,000)
    # EUR, CHF: dot for thousands (100.000)
    # JPY: comma for thousands (100,000)
    if currency in ['EUR', 'CHF']:
        # European style: dot for thousands
        formatted = f'{amount:,.0f}'.replace(',', '.')
    else:
        # US/UK/Japan style: comma for thousands
        formatted = f'{amount:,.0f}'

    # Position symbol based on currency convention
    if currency in ['USD', 'GBP']:
        return f'{symbol}{formatted}'
    else:
        return f'{formatted} {symbol}'