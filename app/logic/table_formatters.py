"""Business logic for formatting DataFrames into AG Grid table structures.

This module contains pure functions for transforming pandas DataFrames into
AG Grid-compatible column definitions and row data. All functions are testable
and have no UI dependencies.
"""

from datetime import datetime

import pandas as pd

from app.core.constants import (
    AGGRID_COL_DATE_MIN_WIDTH,
    AGGRID_COL_DATE_WIDTH,
    AGGRID_COL_MIN_WIDTH,
    COL_DATE,
    COL_DATE_DT,
)
from app.logic.monetary_parsing import parse_monetary_value


def _is_date_col(col: object) -> bool:
    """Check if a column is a date column (Date or date_dt), handling tuples."""
    if col == COL_DATE_DT or col == COL_DATE:
        return True
    return isinstance(col, tuple) and (COL_DATE_DT in col or COL_DATE in col)


def _flatten_field_name(col_key: object) -> str:
    """Convert a column key (string or tuple) to a flat AG Grid field name."""
    if isinstance(col_key, tuple) and len(col_key) == 2:
        category, item = col_key[0].strip(), col_key[1].strip()
        return f"{category}_{item}".replace(" ", "_")
    return str(col_key)


def _format_date_value(date_value: object) -> str:
    """Format a date value to YYYY-MM string."""
    if date_value is None or pd.isna(date_value):
        return ""
    if isinstance(date_value, (pd.Timestamp, datetime)):
        return date_value.strftime("%Y-%m")
    try:
        return pd.to_datetime(date_value).strftime("%Y-%m")
    except Exception:
        return str(date_value)


def _extract_date_from_record(record: dict) -> object:
    """Find and return the date value from a row record."""
    if COL_DATE_DT in record:
        return record[COL_DATE_DT]
    for key in record:
        if key == COL_DATE or (isinstance(key, tuple) and COL_DATE in key):
            return record[key]
    return None


def parse_dataframe_monetary_values(df: pd.DataFrame) -> pd.DataFrame:
    """Parse monetary values in DataFrame to numeric, preserving multi-level column structure.

    Takes a DataFrame with formatted monetary strings (e.g., "1.234,56 €") and converts
    them to clean numeric values (e.g., 1234.56), while preserving the original column
    structure including multi-level headers.

    Args:
        df: DataFrame with formatted monetary values and potentially multi-level columns.

    Returns:
        New DataFrame with same column structure but numeric values.

    Example:
        >>> df = pd.DataFrame({("Cash", "Checking"): ["100,00 €"], ("Cash", "Savings"): ["200 €"]})
        >>> result = parse_dataframe_monetary_values(df)
        >>> result[("Cash", "Checking")][0]
        100.0
    """
    df_clean = df.copy()

    # Iterate through all columns and parse monetary values
    for col in df_clean.columns:
        if _is_date_col(col):
            continue

        # Parse each value in the column
        df_clean[col] = df_clean[col].apply(
            lambda x: parse_monetary_value(x) if not pd.isna(x) else 0.0
        )

    return df_clean


def build_aggrid_columns_from_dataframe(df: pd.DataFrame, currency_formatter: str) -> list[dict]:
    """Build AG Grid columnDefs dynamically from DataFrame with multi-level header support.

    Supports both single-level columns (str) and multi-level columns (tuple).
    Multi-level columns are grouped under their category (first level).

    Args:
        df: DataFrame with single or multi-level columns.
        currency_formatter: JavaScript valueFormatter string for currency values.

    Returns:
        List of AG Grid column definitions with groups for multi-level headers.

    Example:
        Single-level: ["Date", "Cash", "Savings"] → 3 columns
        Multi-level: [("Date", ""), ("Cash", "Checking"), ("Cash", "Savings")]
                   → Date column + Cash group with 2 children
    """
    # Date column always first, pinned, sorted descending
    column_defs: list[dict] = [
        {
            "field": "Date",
            "headerName": "Date",
            "sortable": True,
            "sort": "desc",
            "pinned": "left",
            "minWidth": AGGRID_COL_DATE_MIN_WIDTH,
            "width": AGGRID_COL_DATE_WIDTH,
        }
    ]

    # Group columns by category (for multi-level) or individual (for single-level)
    column_groups: dict[str, list[tuple[str | None, str]]] = {}

    for col in df.columns:
        if _is_date_col(col):
            continue

        if isinstance(col, tuple) and len(col) == 2:
            # Multi-level: (category, item)
            category, item = col[0].strip(), col[1].strip()
            if not category or not item:
                continue
            if category not in column_groups:
                column_groups[category] = []
            column_groups[category].append((category, item))
        else:
            # Single-level: treat as standalone column
            item = str(col)
            if item not in column_groups:
                column_groups[item] = []
            column_groups[item].append((None, item))

    # Build column definitions from groups
    for category, items in column_groups.items():
        if len(items) == 1 and items[0][0] is None:
            # Single-level column: no grouping needed
            item = items[0][1]
            column_defs.append(
                {
                    "field": item,
                    "headerName": item,
                    "sortable": True,
                    "type": "rightAligned",
                    "valueFormatter": currency_formatter,
                    "cellStyle": {"fontFamily": "monospace"},
                    "minWidth": AGGRID_COL_MIN_WIDTH,
                    "flex": 1,
                }
            )
        else:
            # Multi-level: create column group with children
            children = []
            for cat, item in items:
                # Create field name: Category_Item (internal identifier)
                field_name = f"{cat}_{item}".replace(" ", "_")
                children.append(
                    {
                        "field": field_name,
                        "headerName": item,  # User sees only item name
                        "sortable": True,
                        "type": "rightAligned",
                        "valueFormatter": currency_formatter,
                        "cellStyle": {"fontFamily": "monospace"},
                        "minWidth": AGGRID_COL_MIN_WIDTH,
                        "flex": 1,
                    }
                )

            column_defs.append(
                {
                    "headerName": category,  # Group header
                    "children": children,
                }
            )

    return column_defs


def prepare_dataframe_for_aggrid(df: pd.DataFrame) -> list[dict]:
    """Prepare DataFrame rows for AG Grid with flattened column names.

    Converts DataFrame to list of dictionaries, flattening multi-level columns
    to match the field names in columnDefs (Category_Item format).

    Args:
        df: DataFrame with single or multi-level columns.

    Returns:
        List of row dictionaries ready for AG Grid rowData.
    """
    rows = []

    # Convert DataFrame to list of dicts (handles multi-index automatically)
    df_records = df.to_dict("records")

    for record in df_records:
        row_dict: dict[str, str | float] = {}
        row_dict["Date"] = _format_date_value(_extract_date_from_record(record))

        for col_key, value in record.items():
            if _is_date_col(col_key):
                continue

            parsed_value = parse_monetary_value(value)
            if parsed_value is None:
                parsed_value = 0.0

            row_dict[_flatten_field_name(col_key)] = parsed_value

        rows.append(row_dict)

    return rows
