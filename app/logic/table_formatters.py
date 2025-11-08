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
        # Skip date columns (both original and computed)
        if col == COL_DATE_DT or col == COL_DATE:
            continue
        if isinstance(col, tuple) and (COL_DATE in col or COL_DATE_DT in col):
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

        # Extract and format date
        date_value = None
        if COL_DATE_DT in record:
            date_value = record[COL_DATE_DT]
        else:
            # Try to find Date in record keys (for multi-index)
            for key in record:
                if isinstance(key, tuple) and COL_DATE in key:
                    date_value = record[key]
                    break
                elif key == COL_DATE:
                    date_value = record[key]
                    break

        # Format date value
        if date_value is not None and not pd.isna(date_value):
            if isinstance(date_value, (pd.Timestamp, datetime)):
                row_dict["Date"] = date_value.strftime("%Y-%m")
            else:
                try:
                    row_dict["Date"] = pd.to_datetime(date_value).strftime("%Y-%m")
                except Exception:
                    row_dict["Date"] = str(date_value)
        else:
            row_dict["Date"] = ""

        # Process all other columns
        for col_key, value in record.items():
            # Skip date columns (already handled)
            if col_key == COL_DATE_DT or col_key == COL_DATE:
                continue
            if isinstance(col_key, tuple) and (COL_DATE in col_key or COL_DATE_DT in col_key):
                continue

            # Parse monetary value using the same parser as finance_calculator
            parsed_value = parse_monetary_value(value)
            if parsed_value is None:
                parsed_value = 0.0

            # Create field name matching columnDefs
            if isinstance(col_key, tuple) and len(col_key) == 2:
                # Multi-level: flatten to Category_Item
                category, item = col_key[0].strip(), col_key[1].strip()
                field_name = f"{category}_{item}".replace(" ", "_")
            else:
                # Single-level: use column name as-is
                field_name = str(col_key)

            row_dict[field_name] = parsed_value

        rows.append(row_dict)

    return rows
