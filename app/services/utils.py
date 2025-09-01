import locale
import pandas as pd
from user_agents import parse
from io import StringIO
from typing import Any, Callable, Optional, TypeVar

T = TypeVar('T')

def get_or_store(dict: dict[str, Any], key: str, compute_fn: Callable[[], T]) -> T:
    if key not in dict:
        dict[key] = compute_fn()
    return dict[key]

def get_user_agent(http_agent: Optional[str]) -> str:
    return "mobile" if http_agent and parse(http_agent).is_mobile else "desktop"

def read_json(data: str) -> pd.DataFrame:
    return pd.read_json(StringIO(data), orient='split')

def format_currency(amount: float) -> str:
    """Format amount as currency based on system locale"""
    try:
        return locale.currency(amount, grouping=True)
    except Exception:
        # Fallback to no currency formatting if locale setup fails
        return '{:.0f}'.format(amount)