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

def format_currency(amount: float) -> str:
    """Format amount as currency based on system locale."""
    try:
        return locale.currency(amount, grouping=True)
    except Exception:
        # Fallback to no currency formatting if locale setup fails
        return '{:.0f}'.format(amount)