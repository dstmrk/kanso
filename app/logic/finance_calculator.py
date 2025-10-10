# app/logic/finance_calculator.py

import logging
import re
from typing import Any

import pandas as pd

from app.core.constants import (
    CATEGORY_ASSETS,
    CATEGORY_EXPENSES,
    CATEGORY_LIABILITIES,
    CATEGORY_SAVINGS,
    COL_AMOUNT,
    COL_AMOUNT_PARSED,
    COL_CATEGORY,
    COL_DATE,
    COL_DATE_DT,
    COL_EXPENSES,
    COL_EXPENSES_PARSED,
    COL_INCOME,
    COL_INCOME_PARSED,
    COL_MONTH,
    COL_NET_WORTH,
    COL_NET_WORTH_PARSED,
    DATE_FORMAT_DISPLAY,
    DATE_FORMAT_STORAGE,
    MONETARY_COLUMNS,
    MONTHS_IN_YEAR,
    MONTHS_LOOKBACK_YEAR,
)

logger = logging.getLogger(__name__)

# Currency format configuration: (thousand_separator, decimal_separator, has_decimals)
CURRENCY_CONFIG: dict[str, tuple[str, str, bool]] = {
    "EUR": (".", ",", True),  # European format: 1.234,56
    "CHF": (".", ",", True),  # Swiss format: 1.234,56
    "USD": (",", ".", True),  # US format: 1,234.56
    "GBP": (",", ".", True),  # UK format: 1,234.56
    "JPY": (",", "", False),  # Japanese: no decimals: 1,234
}


def detect_currency(value: str) -> str | None:
    """
    Detect currency from symbol in string.

    Args:
        value: String potentially containing currency symbol

    Returns:
        Currency code (EUR, USD, GBP, CHF, JPY) or None if not detected
    """
    if "€" in value:
        return "EUR"
    elif "$" in value:
        return "USD"
    elif "£" in value:
        return "GBP"
    elif "Fr" in value or "CHF" in value:
        return "CHF"
    elif "¥" in value or "JPY" in value:
        return "JPY"
    return None


def parse_monetary_value(value: Any, currency: str | None = None) -> float:
    """
    Parse monetary value with intelligent currency detection.

    Supports multiple currency formats:
    - EUR, CHF: European format (1.234,56)
    - USD, GBP: US/UK format (1,234.56)
    - JPY: No decimals (1,234)

    Args:
        value: Monetary value as string, int, or float
        currency: Optional currency override (EUR, USD, GBP, CHF, JPY)

    Returns:
        Parsed float value. Returns 0.0 for None, empty strings, or unparseable values.

    Examples:
        >>> parse_monetary_value("€ 1.234,56")
        1234.56
        >>> parse_monetary_value("$1,234.56")
        1234.56
        >>> parse_monetary_value("¥1,234")
        1234.0
        >>> parse_monetary_value("1234.56", currency="EUR")
        123456.0  # Interprets as European: dot = thousand separator
    """
    if not isinstance(value, str):
        return float(value) if value is not None else 0.0

    # Detect or use provided currency
    detected_currency = currency or detect_currency(value)

    # Get format config (default to EUR if not found)
    thousand_sep, decimal_sep, has_decimals = CURRENCY_CONFIG.get(
        detected_currency, CURRENCY_CONFIG["EUR"]
    )

    try:
        # Remove currency symbols and extra spaces
        cleaned = re.sub(r"[€$£¥]|Fr|CHF|JPY|USD|EUR|GBP", "", value).strip()
        cleaned = cleaned.replace(" ", "")

        # Special case: plain number without currency symbol
        # If no currency was detected, treat dots/commas intelligently:
        # - If only one separator exists, it's likely decimal (most common case)
        # - Format like "1234.56" or "1234,56" should be treated as decimal
        if detected_currency is None:
            # Count separators
            dot_count = cleaned.count(".")
            comma_count = cleaned.count(",")

            # Only one type of separator
            if dot_count == 1 and comma_count == 0:
                # Single dot - likely decimal point (standard notation)
                return float(cleaned)
            elif comma_count == 1 and dot_count == 0:
                # Single comma - likely decimal (European)
                return float(cleaned.replace(",", "."))
            elif dot_count == 0 and comma_count == 0:
                # No separators - plain integer or float
                return float(cleaned) if cleaned else 0.0
            # Multiple separators - fall through to currency-specific logic

        # Handle the case where there are no separators (plain number)
        if thousand_sep not in cleaned and (not decimal_sep or decimal_sep not in cleaned):
            # No separators found - treat as plain number
            return float(cleaned) if cleaned else 0.0

        # Remove thousand separator
        if thousand_sep:
            cleaned = cleaned.replace(thousand_sep, "")

        # Replace decimal separator with dot (Python standard)
        if decimal_sep and decimal_sep != ".":
            cleaned = cleaned.replace(decimal_sep, ".")

        return float(cleaned) if cleaned else 0.0

    except (ValueError, TypeError):
        logger.warning(f"Failed to parse monetary value: {value}")
        return 0.0


class FinanceCalculator:
    """Optimized finance calculator with cached DataFrame preprocessing."""

    def __init__(
        self,
        df: pd.DataFrame,
        assets_df: pd.DataFrame | None = None,
        liabilities_df: pd.DataFrame | None = None,
        expenses_df: pd.DataFrame | None = None,
    ) -> None:
        self.original_df = df
        self.expenses_df = expenses_df
        self.assets_df = assets_df
        self.liabilities_df = liabilities_df
        self._processed_df = None
        self._processed_expenses_df = None
        self._processed_assets_df = None
        self._processed_liabilities_df = None

    @property
    def processed_df(self) -> pd.DataFrame:
        """Lazily processed and cached main DataFrame."""
        if self._processed_df is None:
            self._processed_df = self._preprocess_main_df()
        return self._processed_df

    @property
    def processed_expenses_df(self) -> pd.DataFrame | None:
        """Lazily processed and cached expenses DataFrame."""
        if self.expenses_df is not None and self._processed_expenses_df is None:
            self._processed_expenses_df = self._preprocess_expenses_df()
        return self._processed_expenses_df

    @property
    def processed_assets_df(self) -> pd.DataFrame | None:
        """Lazily processed and cached assets DataFrame."""
        if self.assets_df is not None and self._processed_assets_df is None:
            self._processed_assets_df = self._preprocess_assets_df()
        return self._processed_assets_df

    @property
    def processed_liabilities_df(self) -> pd.DataFrame | None:
        """Lazily processed and cached liabilities DataFrame."""
        if self.liabilities_df is not None and self._processed_liabilities_df is None:
            self._processed_liabilities_df = self._preprocess_liabilities_df()
        return self._processed_liabilities_df

    def _preprocess_main_df(self) -> pd.DataFrame:
        """Preprocess main DataFrame once with all required transformations."""
        df = self.original_df.copy()
        df[COL_DATE_DT] = pd.to_datetime(df[COL_DATE], errors="coerce")
        df = df.sort_values(by=COL_DATE_DT)

        # Parse monetary columns once
        for col in MONETARY_COLUMNS:
            if col in df.columns:
                df[f'{col.lower().replace(" ", "_")}_parsed'] = df[col].apply(parse_monetary_value)

        return df

    def _preprocess_expenses_df(self) -> pd.DataFrame | None:
        """Preprocess expenses DataFrame once."""
        if self.expenses_df is None:
            return None

        df = self.expenses_df.copy()
        df[COL_DATE_DT] = pd.to_datetime(
            df[COL_MONTH].astype(str).str.strip(), format=DATE_FORMAT_STORAGE, errors="coerce"
        )
        df[COL_AMOUNT_PARSED] = df[COL_AMOUNT].apply(parse_monetary_value)
        return df.sort_values(by=COL_DATE_DT)

    def _preprocess_assets_df(self) -> pd.DataFrame | None:
        """Preprocess assets DataFrame once with date parsing and sorting."""
        if self.assets_df is None or self.assets_df.empty:
            return None

        df = self.assets_df.copy()

        # Find Date column (handles MultiIndex)
        date_col = None
        for col in df.columns:
            if isinstance(col, tuple):
                if COL_DATE in col[0] or COL_DATE in col[1]:
                    date_col = col
                    break
            else:
                if COL_DATE in col:
                    date_col = col
                    break

        if date_col is not None:
            df[COL_DATE_DT] = pd.to_datetime(
                df[date_col], format=DATE_FORMAT_STORAGE, errors="coerce"
            )
            df = df.sort_values(by=COL_DATE_DT)

        return df

    def _preprocess_liabilities_df(self) -> pd.DataFrame | None:
        """Preprocess liabilities DataFrame once with date parsing and sorting."""
        if self.liabilities_df is None or self.liabilities_df.empty:
            return None

        df = self.liabilities_df.copy()

        # Find Date column (handles MultiIndex)
        date_col = None
        for col in df.columns:
            if isinstance(col, tuple):
                if any(
                    keyword in col[0] or keyword in col[1]
                    for keyword in [COL_DATE, "Data", COL_CATEGORY]
                ):
                    date_col = col
                    break
            else:
                if any(keyword in col for keyword in [COL_DATE, "Data", COL_CATEGORY]):
                    date_col = col
                    break

        if date_col is not None:
            df[COL_DATE_DT] = pd.to_datetime(
                df[date_col], format=DATE_FORMAT_STORAGE, errors="coerce"
            )
            df = df.sort_values(by=COL_DATE_DT)

        return df

    def _validate_columns(self, required_columns: list[str]) -> bool:
        """Validate required columns exist."""
        missing_cols = [col for col in required_columns if col not in self.original_df.columns]
        if missing_cols:
            logger.error(f"DataFrame missing required columns: {missing_cols}")
            return False
        return True

    def get_current_net_worth(self) -> float:
        """Get the most recent net worth value."""
        if not self._validate_columns([COL_NET_WORTH]):
            return 0.0
        return self.processed_df[COL_NET_WORTH_PARSED].iloc[-1]

    def get_last_update_date(self) -> str:
        """Get the date of the last update in MM-YYYY format."""
        return self.processed_df[COL_DATE_DT].iloc[-1].strftime(DATE_FORMAT_DISPLAY)

    def get_month_over_month_net_worth_variation_percentage(self) -> float:
        """Get month over month net worth percentage change."""
        if not self._validate_columns([COL_NET_WORTH]):
            return 0.0

        df = self.processed_df
        if len(df) < 2:
            return 0.0

        current: float = df["net_worth_parsed"].iloc[-1]
        previous: float = df["net_worth_parsed"].iloc[-2]

        return (current - previous) / previous if previous != 0 else 0.0

    def get_month_over_month_net_worth_variation_absolute(self) -> float:
        """Get month over month net worth absolute change."""
        if not self._validate_columns([COL_NET_WORTH]):
            return 0.0

        df = self.processed_df
        if len(df) < 2:
            return 0.0

        return df["net_worth_parsed"].iloc[-1] - df["net_worth_parsed"].iloc[-2]

    def get_year_over_year_net_worth_variation_percentage(self) -> float:
        """Get year over year net worth percentage change."""
        if not self._validate_columns([COL_NET_WORTH]):
            return 0.0

        df = self.processed_df
        if len(df) < MONTHS_LOOKBACK_YEAR:
            return 0.0

        current: float = df["net_worth_parsed"].iloc[-1]
        previous_year: float = df["net_worth_parsed"].iloc[-MONTHS_LOOKBACK_YEAR]

        return (current - previous_year) / previous_year if previous_year != 0 else 0.0

    def get_year_over_year_net_worth_variation_absolute(self) -> float:
        """Get year over year net worth absolute change."""
        if not self._validate_columns([COL_NET_WORTH]):
            return 0.0

        df = self.processed_df
        if len(df) < MONTHS_LOOKBACK_YEAR:
            return 0.0

        return df["net_worth_parsed"].iloc[-1] - df["net_worth_parsed"].iloc[-MONTHS_LOOKBACK_YEAR]

    def get_average_saving_ratio_last_12_months_percentage(self) -> float:
        """Get average saving ratio for last 12 months as percentage."""
        if not self._validate_columns([COL_INCOME, COL_EXPENSES]):
            return 0.0

        df = self.processed_df
        income: float = df[COL_INCOME_PARSED].iloc[-MONTHS_IN_YEAR:].sum()
        expenses: float = df[COL_EXPENSES_PARSED].iloc[-MONTHS_IN_YEAR:].sum()

        return (income - expenses) / income if income != 0 else 0.0

    def get_average_saving_ratio_last_12_months_absolute(self) -> float:
        """Get average monthly savings for last 12 months."""
        if not self._validate_columns([COL_INCOME, COL_EXPENSES]):
            return 0.0

        df = self.processed_df
        income: float = df[COL_INCOME_PARSED].iloc[-MONTHS_IN_YEAR:].sum()
        expenses: float = df[COL_EXPENSES_PARSED].iloc[-MONTHS_IN_YEAR:].sum()

        return (income - expenses) / MONTHS_IN_YEAR if income != 0 else 0.0

    def get_fi_progress(self) -> float:
        """Get FI progress - placeholder implementation."""
        return 0.263

    def get_monthly_net_worth(self) -> dict[str, list]:
        """Get monthly net worth data for charting."""
        if not self._validate_columns([COL_DATE, COL_NET_WORTH]):
            return {"dates": [], "values": []}

        df = self.processed_df.dropna(subset=[COL_DATE_DT])
        return {
            "dates": df[COL_DATE_DT].dt.strftime(DATE_FORMAT_STORAGE).tolist(),
            "values": df["net_worth_parsed"].tolist(),
        }

    def get_assets_liabilities(self) -> dict[str, dict[str, Any]]:
        """Get assets and liabilities breakdown from the latest data."""
        asset_liabilities: dict[str, dict[str, Any]] = {
            CATEGORY_ASSETS: {},
            CATEGORY_LIABILITIES: {},
        }
        reference_date = None

        # Use preprocessed DataFrames
        assets_df = self.processed_assets_df
        liabilities_df = self.processed_liabilities_df

        if assets_df is not None and not assets_df.empty:
            # Get latest row
            latest_row = assets_df.iloc[-1]
            reference_date = assets_df[COL_DATE_DT].iloc[-1]

            # Extract values dynamically from columns
            for col in assets_df.columns:
                # Skip date_dt column
                if col == "date_dt":
                    continue
                # Skip if column name contains 'date_dt' (handles both tuple and string columns)
                if isinstance(col, tuple) and "date_dt" in col:
                    continue
                # Skip Date column
                if isinstance(col, tuple):
                    if "Date" in col[0] or "Date" in col[1]:
                        continue
                else:
                    if "Date" in col:
                        continue

                if isinstance(col, tuple) and len(col) == 2:
                    # MultiIndex: (category, item)
                    category, item = col
                    category = category.strip()
                    item = item.strip()
                    if not category:
                        continue
                    value = parse_monetary_value(latest_row[col])
                    if category not in asset_liabilities[CATEGORY_ASSETS]:
                        asset_liabilities[CATEGORY_ASSETS][category] = {}
                    asset_liabilities[CATEGORY_ASSETS][category][item] = value
                else:
                    # Single header: column name is the item
                    item = col
                    value = parse_monetary_value(latest_row[col])
                    asset_liabilities[CATEGORY_ASSETS][item] = value

        # Process Liabilities DataFrame
        if liabilities_df is not None and not liabilities_df.empty:
            # Use reference date from Assets to get the corresponding row
            if reference_date is not None:
                matching_rows = liabilities_df[liabilities_df[COL_DATE_DT] <= reference_date]
                if not matching_rows.empty:
                    latest_row = matching_rows.iloc[-1]
                else:
                    latest_row = liabilities_df.iloc[-1]
            else:
                latest_row = liabilities_df.iloc[-1]

            # Extract values dynamically from columns
            for col in liabilities_df.columns:
                # Skip date_dt column
                if col == "date_dt":
                    continue
                # Skip if column name contains 'date_dt' (handles both tuple and string columns)
                if isinstance(col, tuple) and "date_dt" in col:
                    continue
                # Skip Date column
                if isinstance(col, tuple):
                    if any(
                        keyword in col[0] or keyword in col[1]
                        for keyword in ["Date", "Data", COL_CATEGORY]
                    ):
                        continue
                else:
                    if any(keyword in col for keyword in ["Date", "Data", COL_CATEGORY]):
                        continue

                if isinstance(col, tuple) and len(col) == 2:
                    # MultiIndex: (category, item)
                    category, item = col
                    category = category.strip()
                    item = item.strip()
                    if not category or category == COL_CATEGORY:
                        continue
                    value = parse_monetary_value(latest_row[col])
                    if category not in asset_liabilities[CATEGORY_LIABILITIES]:
                        asset_liabilities[CATEGORY_LIABILITIES][category] = {}
                    asset_liabilities[CATEGORY_LIABILITIES][category][item] = value
                else:
                    # Single header: column name is the item
                    item = col
                    value = parse_monetary_value(latest_row[col])
                    asset_liabilities[CATEGORY_LIABILITIES][item] = value

        return asset_liabilities

    def get_cash_flow_last_12_months(self) -> dict[str, float]:
        """Get cash flow data for last 12 months."""
        if not self._validate_columns([COL_INCOME]):
            return {CATEGORY_SAVINGS: 0.0, CATEGORY_EXPENSES: 0.0}

        if self.processed_expenses_df is None:
            return {CATEGORY_SAVINGS: 0.0, CATEGORY_EXPENSES: 0.0}

        # Income from main df
        income = self.processed_df[COL_INCOME_PARSED].iloc[-MONTHS_IN_YEAR:].sum()

        # Expenses from expenses df (last 12 months)
        ef: pd.DataFrame = self.processed_expenses_df
        latest_date: pd.Timestamp = ef[COL_DATE_DT].max()
        start_date: pd.Timestamp = (latest_date - pd.DateOffset(months=MONTHS_IN_YEAR - 1)).replace(
            day=1
        )

        ef_last_12: pd.DataFrame = ef[
            (ef[COL_DATE_DT] >= start_date) & (ef[COL_DATE_DT] <= latest_date)
        ]
        total_expenses: float = ef_last_12[COL_AMOUNT_PARSED].sum()

        # Expenses by category
        expenses_by_category: dict[str, float] = (
            ef_last_12.groupby(COL_CATEGORY)[COL_AMOUNT_PARSED].sum().to_dict()
        )

        result: dict[str, float] = {
            CATEGORY_EXPENSES: total_expenses,
            CATEGORY_SAVINGS: income - total_expenses,
        }
        result.update(expenses_by_category)

        return result

    def get_average_expenses_by_category_last_12_months(self) -> dict[str, float]:
        """Get average expenses by category for last 12 months."""
        if self.processed_expenses_df is None:
            return {}

        ef: pd.DataFrame = self.processed_expenses_df
        latest_date: pd.Timestamp = ef[COL_DATE_DT].max()
        start_date: pd.Timestamp = (latest_date - pd.DateOffset(months=MONTHS_IN_YEAR - 1)).replace(
            day=1
        )

        ef_last_12: pd.DataFrame = ef[
            (ef[COL_DATE_DT] >= start_date) & (ef[COL_DATE_DT] <= latest_date)
        ]
        return ef_last_12.groupby(COL_CATEGORY)[COL_AMOUNT_PARSED].sum().to_dict()

    def get_incomes_vs_expenses(self) -> dict[str, list]:
        """Get income vs expenses data for charting."""
        if not self._validate_columns([COL_DATE, COL_INCOME, COL_EXPENSES]):
            return {"dates": [], "incomes": [], "expenses": []}

        df = self.processed_df.dropna(subset=[COL_DATE_DT]).iloc[-MONTHS_IN_YEAR:]

        return {
            "dates": df[COL_DATE_DT].dt.strftime(DATE_FORMAT_STORAGE).tolist(),
            "incomes": df[COL_INCOME_PARSED].tolist(),
            "expenses": [-x for x in df[COL_EXPENSES_PARSED].tolist()],  # Negative for chart
        }
