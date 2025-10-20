# app/logic/finance_calculator.py
"""Financial calculations and monetary value parsing.

This module provides the core financial calculation logic for the Kanso application.
It includes intelligent multi-currency parsing and a comprehensive calculator class
for computing financial KPIs from monthly data.

Key features:
    - Multi-currency support (EUR, USD, GBP, CHF, JPY)
    - Intelligent format detection (European vs US/UK formats)
    - Cached DataFrame preprocessing for performance
    - Net worth tracking and variation calculations
    - Savings ratio and cash flow analysis

Example:
    >>> from app.logic.finance_calculator import FinanceCalculator, parse_monetary_value
    >>> # Parse various currency formats
    >>> parse_monetary_value("€ 1.234,56")
    1234.56
    >>> parse_monetary_value("$1,234.56")
    1234.56
    >>> # Create calculator instance
    >>> calc = FinanceCalculator(df)
    >>> calc.get_current_net_worth()
    50000.0
"""

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
    COL_INCOME,
    COL_INCOME_PARSED,
    COL_NET_WORTH,
    COL_NET_WORTH_PARSED,
    DATE_FORMAT_DISPLAY,
    DATE_FORMAT_STORAGE,
    MONETARY_COLUMNS,
    MONTHS_IN_YEAR,
    MONTHS_LOOKBACK_YEAR,
)
from app.core.currency_formats import CURRENCY_FORMATS, get_currency_format
from app.core.monitoring import track_performance

logger = logging.getLogger(__name__)


def detect_currency(value: str) -> str | None:
    """Detect currency from symbol in string.

    Args:
        value: String potentially containing currency symbol

    Returns:
        Currency code (EUR, USD, GBP, CHF, JPY) or None if not detected
    """
    # Check for each currency symbol from centralized config
    for currency_code, fmt in CURRENCY_FORMATS.items():
        if fmt.symbol in value:
            return currency_code
    # Also check for currency code strings
    if "CHF" in value:
        return "CHF"
    if "JPY" in value:
        return "JPY"
    return None


def parse_monetary_value(value: Any, currency: str | None = None) -> float:
    """Parse monetary value with intelligent currency detection.

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
    if detected_currency and detected_currency in CURRENCY_FORMATS:
        fmt = get_currency_format(detected_currency)
    else:
        # Default to EUR format
        fmt = get_currency_format("EUR")

    thousand_sep = fmt.thousands_sep
    decimal_sep = fmt.decimal_sep

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
    """Optimized finance calculator with cached DataFrame preprocessing.

    This class provides comprehensive financial calculations including net worth tracking,
    savings ratios, cash flow analysis, and asset/liability breakdowns. It uses lazy
    preprocessing and caching to avoid redundant pandas operations.

    The calculator expects monthly financial data with dates in YYYY-MM format and
    supports multiple currency formats for monetary values.

    Attributes:
        original_df: The raw main DataFrame with Date, Net Worth, Income, Expenses columns
        expenses_df: Optional expenses breakdown DataFrame
        assets_df: Optional assets breakdown DataFrame
        liabilities_df: Optional liabilities breakdown DataFrame

    Example:
        >>> df = pd.DataFrame({
        ...     'Date': ['2024-01', '2024-02'],
        ...     'Net Worth': ['€ 10.000', '€ 11.000'],
        ...     'Income': ['€ 3.000', '€ 3.000'],
        ...     'Expenses': ['€ 2.000', '€ 2.000']
        ... })
        >>> calc = FinanceCalculator(df)
        >>> calc.get_current_net_worth()
        11000.0
        >>> calc.get_month_over_month_net_worth_variation_percentage()
        0.1
    """

    def __init__(
        self,
        df: pd.DataFrame,
        assets_df: pd.DataFrame | None = None,
        liabilities_df: pd.DataFrame | None = None,
        expenses_df: pd.DataFrame | None = None,
        incomes_df: pd.DataFrame | None = None,
    ) -> None:
        """Initialize the calculator with financial data.

        Args:
            df: Main DataFrame containing Date, Net Worth, Income, and Expenses columns
            assets_df: Optional DataFrame with detailed asset breakdown (supports MultiIndex)
            liabilities_df: Optional DataFrame with detailed liability breakdown (supports MultiIndex)
            expenses_df: Optional DataFrame with Month, Category, and Amount columns
            incomes_df: Optional DataFrame with detailed income breakdown (supports MultiIndex)

        Note:
            DataFrames are not processed immediately. Processing happens lazily when
            data is first accessed through properties like `processed_df`.
        """
        self.original_df = df
        self.expenses_df = expenses_df
        self.assets_df = assets_df
        self.liabilities_df = liabilities_df
        self.incomes_df = incomes_df
        self._processed_df = None
        self._processed_expenses_df = None
        self._processed_assets_df = None
        self._processed_liabilities_df = None
        self._processed_incomes_df = None

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

    @property
    def processed_incomes_df(self) -> pd.DataFrame | None:
        """Lazily processed and cached incomes DataFrame."""
        if self.incomes_df is not None and self._processed_incomes_df is None:
            self._processed_incomes_df = self._preprocess_incomes_df()
        return self._processed_incomes_df

    def _get_monthly_expenses_totals(self) -> pd.DataFrame | None:
        """Calculate monthly expense totals from detailed Expenses sheet.

        Aggregates all expense transactions by month, summing amounts to get
        monthly totals. This replaces the Expenses column from the Data sheet.

        Returns:
            DataFrame with columns [Month, total_expenses] indexed by month datetime,
            or None if expenses_df is not available

        Example:
            Month       total_expenses
            2024-01     2000.0
            2024-02     2100.0
        """
        if self.processed_expenses_df is None:
            return None

        ef = self.processed_expenses_df

        # Check required columns exist
        if COL_DATE_DT not in ef.columns or COL_AMOUNT_PARSED not in ef.columns:
            logger.error("Expenses sheet missing required parsed columns")
            return None

        # Group by month and sum amounts
        monthly_totals = (
            ef.groupby(COL_DATE_DT)[COL_AMOUNT_PARSED]
            .sum()
            .reset_index()
            .rename(columns={COL_AMOUNT_PARSED: "total_expenses"})
        )

        return monthly_totals

    def _preprocess_main_df(self) -> pd.DataFrame:
        """Preprocess main DataFrame once with all required transformations.

        Performs the following operations:
        - Converts Date column to datetime objects
        - Sorts by date
        - Parses all monetary columns (Net Worth, Income, Expenses, etc.) to float

        Returns:
            Preprocessed DataFrame with additional parsed columns and date_dt column

        Note:
            This method is called lazily only once when `processed_df` is first accessed.
            The result is cached to avoid redundant processing.
        """
        df = self.original_df.copy()
        df[COL_DATE_DT] = pd.to_datetime(df[COL_DATE], errors="coerce")
        df = df.sort_values(by=COL_DATE_DT)

        # Parse monetary columns once
        for col in MONETARY_COLUMNS:
            if col in df.columns:
                df[f'{col.lower().replace(" ", "_")}_parsed'] = df[col].apply(parse_monetary_value)

        return df

    def _preprocess_expenses_df(self) -> pd.DataFrame | None:
        """Preprocess expenses DataFrame once.

        Converts Date column to datetime, parses Amount column to float, and sorts by date.

        Returns:
            Preprocessed expenses DataFrame with date_dt and amount_parsed columns,
            or None if no expenses DataFrame was provided
        """
        if self.expenses_df is None:
            return None

        df = self.expenses_df.copy()

        # Check if Date column exists
        if COL_DATE not in df.columns:
            logger.error(
                f"Expenses sheet missing '{COL_DATE}' column! Available: {df.columns.tolist()}"
            )
            return None

        # Check if dates are already datetime objects (from Google Sheets)
        if pd.api.types.is_datetime64_any_dtype(df[COL_DATE]):
            # Dates are already datetime objects - just normalize to first day of month
            df[COL_DATE_DT] = pd.to_datetime(df[COL_DATE]).dt.to_period("M").dt.to_timestamp()
        else:
            # Dates are strings - parse them
            df[COL_DATE_DT] = pd.to_datetime(
                df[COL_DATE].astype(str).str.strip(), format=DATE_FORMAT_STORAGE, errors="coerce"
            )

        # Warn if too many dates failed to parse
        nat_count = df[COL_DATE_DT].isna().sum()
        if nat_count > 0:
            logger.warning(f"Failed to parse {nat_count} dates in Expenses sheet")

        # Check if Amount column exists
        if COL_AMOUNT not in df.columns:
            logger.error(
                f"Expenses sheet missing '{COL_AMOUNT}' column! Available: {df.columns.tolist()}"
            )
            return None

        df[COL_AMOUNT_PARSED] = df[COL_AMOUNT].apply(parse_monetary_value)

        return df.sort_values(by=COL_DATE_DT)

    def _preprocess_assets_df(self) -> pd.DataFrame | None:
        """Preprocess assets DataFrame once with date parsing and sorting.

        Handles both single-level and MultiIndex column structures. Locates the Date
        column dynamically and converts it to datetime for sorting.

        Returns:
            Preprocessed assets DataFrame with date_dt column, or None if no assets
            DataFrame was provided
        """
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
        """Preprocess liabilities DataFrame once with date parsing and sorting.

        Handles both single-level and MultiIndex column structures. Locates the Date
        column dynamically and converts it to datetime for sorting.

        Returns:
            Preprocessed liabilities DataFrame with date_dt column, or None if no
            liabilities DataFrame was provided
        """
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

    def _preprocess_incomes_df(self) -> pd.DataFrame | None:
        """Preprocess incomes DataFrame once with date parsing and sorting.

        Handles both single-level and MultiIndex column structures. Locates the Date
        column dynamically and converts it to datetime for sorting.

        Returns:
            Preprocessed incomes DataFrame with date_dt column, or None if no
            incomes DataFrame was provided
        """
        if self.incomes_df is None or self.incomes_df.empty:
            return None

        df = self.incomes_df.copy()

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

    def _validate_columns(self, required_columns: list[str]) -> bool:
        """Validate that required columns exist in the original DataFrame.

        Args:
            required_columns: List of column names that must be present

        Returns:
            True if all required columns exist, False otherwise

        Note:
            Logs an error message listing missing columns if validation fails.
        """
        missing_cols = [col for col in required_columns if col not in self.original_df.columns]
        if missing_cols:
            logger.error(f"DataFrame missing required columns: {missing_cols}")
            return False
        return True

    def _get_total_income_for_period(
        self, start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None
    ) -> float:
        """Calculate total income from incomes_df for a specific period.

        Supports both single-index and multi-index Incomes DataFrames. If incomes_df
        is not available, falls back to using the Income column from main DataFrame.

        Args:
            start_date: Optional start date for filtering (inclusive)
            end_date: Optional end date for filtering (inclusive)

        Returns:
            Total income for the specified period as float

        Note:
            If no incomes_df is provided, this method falls back to the Income column
            from the main DataFrame for backward compatibility.
        """
        # Fallback to main DataFrame Income column if no incomes_df
        if self.processed_incomes_df is None:
            if COL_INCOME not in self.original_df.columns:
                return 0.0

            df = self.processed_df
            if start_date is not None:
                df = df[df[COL_DATE_DT] >= start_date]
            if end_date is not None:
                df = df[df[COL_DATE_DT] <= end_date]

            return df[COL_INCOME_PARSED].sum()

        # Use incomes_df
        df = self.processed_incomes_df

        # Check if date_dt column exists (preprocessing might have failed)
        if COL_DATE_DT not in df.columns:
            logger.warning("date_dt column not found in incomes_df, using all data")
        else:
            # Filter by date range if specified
            if start_date is not None:
                df = df[df[COL_DATE_DT] >= start_date]
            if end_date is not None:
                df = df[df[COL_DATE_DT] <= end_date]

        # Calculate total income by summing all monetary columns
        total = 0.0
        for col in df.columns:
            # Skip date_dt column (exact match for both single and tuple)
            if col == COL_DATE_DT or col == "date_dt":
                continue

            # Skip tuple columns that contain date_dt (like ('date_dt', ''))
            if isinstance(col, tuple) and any("date_dt" in str(c).lower() for c in col):
                continue

            # Skip Date columns (handle both tuple and string)
            # IMPORTANT: Only check for "Date" (capital D), not "data" (which might be a valid category)
            if isinstance(col, tuple):
                # MultiIndex: check if any level contains "Date" exactly
                if any("Date" in str(c) for c in col):
                    continue
            else:
                # Single-level: check if column name contains "Date"
                if "Date" in str(col):
                    continue

            # Sum all monetary columns
            try:
                total += df[col].apply(parse_monetary_value).sum()
            except Exception as e:
                logger.warning(f"Failed to parse income column '{col}': {e}")
                continue

        return total

    def get_current_net_worth(self) -> float:
        """Get the most recent net worth value.

        Returns:
            Current net worth as float, or 0.0 if Net Worth column is missing
        """
        if not self._validate_columns([COL_NET_WORTH]):
            return 0.0
        return self.processed_df[COL_NET_WORTH_PARSED].iloc[-1]

    def get_last_update_date(self) -> str:
        """Get the date of the last update.

        Returns:
            Date string in MM-YYYY format (e.g., "01-2025")
        """
        return self.processed_df[COL_DATE_DT].iloc[-1].strftime(DATE_FORMAT_DISPLAY)

    def get_month_over_month_net_worth_variation_percentage(self) -> float:
        """Get month-over-month net worth percentage change.

        Calculates the relative change between the last two months.

        Returns:
            Percentage change as decimal (e.g., 0.05 for 5% increase),
            or 0.0 if insufficient data or Net Worth column is missing

        Example:
            If net worth went from €20,000 to €21,000, returns 0.05 (5% increase)
        """
        if not self._validate_columns([COL_NET_WORTH]):
            return 0.0

        df = self.processed_df
        if len(df) < 2:
            return 0.0

        current: float = df["net_worth_parsed"].iloc[-1]
        previous: float = df["net_worth_parsed"].iloc[-2]

        return (current - previous) / previous if previous != 0 else 0.0

    def get_month_over_month_net_worth_variation_absolute(self) -> float:
        """Get month-over-month net worth absolute change.

        Calculates the absolute difference between the last two months.

        Returns:
            Absolute change in currency units (e.g., 1000.0 for €1,000 increase),
            or 0.0 if insufficient data or Net Worth column is missing

        Example:
            If net worth went from €20,000 to €21,000, returns 1000.0
        """
        if not self._validate_columns([COL_NET_WORTH]):
            return 0.0

        df = self.processed_df
        if len(df) < 2:
            return 0.0

        return df["net_worth_parsed"].iloc[-1] - df["net_worth_parsed"].iloc[-2]

    def get_year_over_year_net_worth_variation_percentage(self) -> float:
        """Get year-over-year net worth percentage change.

        Compares current net worth with the value from 13 months ago.

        Returns:
            Percentage change as decimal (e.g., 1.2 for 120% increase),
            or 0.0 if insufficient data (less than 13 months) or Net Worth column is missing

        Example:
            If net worth went from €10,000 to €22,000, returns 1.2 (120% increase)
        """
        if not self._validate_columns([COL_NET_WORTH]):
            return 0.0

        df = self.processed_df
        if len(df) < MONTHS_LOOKBACK_YEAR:
            return 0.0

        current: float = df["net_worth_parsed"].iloc[-1]
        previous_year: float = df["net_worth_parsed"].iloc[-MONTHS_LOOKBACK_YEAR]

        return (current - previous_year) / previous_year if previous_year != 0 else 0.0

    def get_year_over_year_net_worth_variation_absolute(self) -> float:
        """Get year-over-year net worth absolute change.

        Compares current net worth with the value from 13 months ago.

        Returns:
            Absolute change in currency units (e.g., 12000.0 for €12,000 increase),
            or 0.0 if insufficient data (less than 13 months) or Net Worth column is missing

        Example:
            If net worth went from €10,000 to €22,000, returns 12000.0
        """
        if not self._validate_columns([COL_NET_WORTH]):
            return 0.0

        df = self.processed_df
        if len(df) < MONTHS_LOOKBACK_YEAR:
            return 0.0

        return df["net_worth_parsed"].iloc[-1] - df["net_worth_parsed"].iloc[-MONTHS_LOOKBACK_YEAR]

    def get_average_saving_ratio_last_12_months_percentage(self) -> float:
        """Get average saving ratio for last 12 months as percentage.

        Calculates (total income - total expenses) / total income for the last 12 months.
        Uses incomes_df if available, otherwise falls back to Income column from main DataFrame.
        Expenses are calculated from the detailed Expenses sheet.

        Returns:
            Saving ratio as decimal (e.g., 0.33 for 33% savings rate),
            or 0.0 if expenses data is missing

        Example:
            If income is €36,000 and expenses are €24,000, returns 0.33 (33% savings rate)
        """
        # Get monthly expense totals from Expenses sheet
        monthly_expenses = self._get_monthly_expenses_totals()
        if monthly_expenses is None or monthly_expenses.empty:
            logger.warning("No expenses data available for saving ratio calculation")
            return 0.0

        # Get date range for last 12 months
        latest_date = monthly_expenses[COL_DATE_DT].max()
        start_date = (latest_date - pd.DateOffset(months=MONTHS_IN_YEAR - 1)).replace(day=1)

        logger.debug(
            f"Saving ratio calculation period: {start_date.strftime(DATE_FORMAT_STORAGE)} to {latest_date.strftime(DATE_FORMAT_STORAGE)}"
        )

        # Calculate income using helper method
        income: float = self._get_total_income_for_period(start_date, latest_date)

        # Calculate expenses from aggregated monthly totals
        expenses_last_12 = monthly_expenses[monthly_expenses[COL_DATE_DT] >= start_date]
        expenses: float = expenses_last_12["total_expenses"].sum()

        logger.debug(
            f"Saving ratio: income={income}, expenses={expenses}, months={len(expenses_last_12)}"
        )

        if income == 0:
            logger.warning("Income is 0, cannot calculate saving ratio")
            return 0.0

        ratio = (income - expenses) / income
        logger.debug(f"Calculated saving ratio: {ratio:.2%}")
        return ratio

    def get_average_saving_ratio_last_12_months_absolute(self) -> float:
        """Get average monthly savings for last 12 months.

        Calculates (total income - total expenses) / 12 for the last 12 months.
        Uses incomes_df if available, otherwise falls back to Income column from main DataFrame.
        Expenses are calculated from the detailed Expenses sheet.

        Returns:
            Average monthly savings in currency units (e.g., 1000.0 for €1,000/month),
            or 0.0 if expenses data is missing

        Example:
            If total savings over 12 months is €12,000, returns 1000.0 (€1,000/month average)
        """
        # Get monthly expense totals from Expenses sheet
        monthly_expenses = self._get_monthly_expenses_totals()
        if monthly_expenses is None or monthly_expenses.empty:
            return 0.0

        # Get date range for last 12 months
        latest_date = monthly_expenses[COL_DATE_DT].max()
        start_date = (latest_date - pd.DateOffset(months=MONTHS_IN_YEAR - 1)).replace(day=1)

        # Calculate income using helper method
        income: float = self._get_total_income_for_period(start_date, latest_date)

        # Calculate expenses from aggregated monthly totals
        expenses_last_12 = monthly_expenses[monthly_expenses[COL_DATE_DT] >= start_date]
        expenses: float = expenses_last_12["total_expenses"].sum()

        return (income - expenses) / MONTHS_IN_YEAR if income != 0 else 0.0

    def get_fi_progress(self) -> float:
        """Get Financial Independence (FI) progress.

        Returns:
            FI progress as decimal (e.g., 0.263 for 26.3% progress toward FI goal)

        Note:
            This is currently a placeholder implementation returning a fixed value.
            Should be implemented based on user's FI number and current net worth.
        """
        return 0.263

    @track_performance("get_monthly_net_worth")
    def get_monthly_net_worth(self) -> dict[str, list]:
        """Get monthly net worth data for charting.

        Returns:
            Dictionary with 'dates' (list of YYYY-MM strings) and 'values' (list of floats),
            or empty lists if Date or Net Worth columns are missing

        Example:
            {
                'dates': ['2024-01', '2024-02', '2024-03'],
                'values': [10000.0, 11000.0, 12000.0]
            }
        """
        if not self._validate_columns([COL_DATE, COL_NET_WORTH]):
            return {"dates": [], "values": []}

        df = self.processed_df.dropna(subset=[COL_DATE_DT])
        return {
            "dates": df[COL_DATE_DT].dt.strftime(DATE_FORMAT_STORAGE).tolist(),
            "values": df["net_worth_parsed"].tolist(),
        }

    @track_performance("get_assets_liabilities")
    def get_assets_liabilities(self) -> dict[str, dict[str, Any]]:
        """Get assets and liabilities breakdown from the latest data.

        Extracts values from the most recent row of assets_df and liabilities_df.
        Supports both single-level columns and MultiIndex columns (category, item).

        Returns:
            Dictionary with 'Assets' and 'Liabilities' keys, each containing nested
            dictionaries of categories and their values

        Example:
            {
                'Assets': {
                    'Cash': 5000.0,
                    'Stocks': {'AAPL': 10000.0, 'GOOGL': 8000.0}
                },
                'Liabilities': {
                    'Mortgage': 200000.0
                }
            }
        """
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

    @track_performance("get_cash_flow_last_12_months")
    def get_cash_flow_last_12_months(self) -> dict[str, float]:
        """Get cash flow data for last 12 months.

        Calculates total income, total expenses, and savings for the last 12 months.
        Also includes breakdown by expense categories if expenses_df is available.
        Uses incomes_df if available, otherwise falls back to Income column from main DataFrame.

        Returns:
            Dictionary with 'Savings', 'Expenses', and category keys mapping to float values

        Example:
            {
                'Savings': 12000.0,
                'Expenses': 24000.0,
                'Food': 6000.0,
                'Transport': 3000.0,
                'Housing': 15000.0
            }
        """
        if self.processed_expenses_df is None:
            return {CATEGORY_SAVINGS: 0.0, CATEGORY_EXPENSES: 0.0}

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

        # Income using helper method
        income = self._get_total_income_for_period(start_date, latest_date)

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

    @track_performance("get_average_expenses_by_category_last_12_months")
    def get_average_expenses_by_category_last_12_months(self) -> dict[str, float]:
        """Get total expenses by category for last 12 months.

        Returns:
            Dictionary mapping category names to total expense amounts,
            or empty dict if expenses_df is not available

        Example:
            {'Food': 6000.0, 'Transport': 3000.0, 'Housing': 15000.0}
        """
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

    @track_performance("get_incomes_vs_expenses")
    def get_incomes_vs_expenses(self) -> dict[str, list]:
        """Get income vs expenses data for charting last 12 months.

        Uses incomes_df if available, otherwise falls back to Income column from main DataFrame.
        Expenses are calculated from the detailed Expenses sheet.

        Returns:
            Dictionary with 'dates' (YYYY-MM strings), 'incomes' (positive floats),
            and 'expenses' (negative floats for chart display),
            or empty lists if required columns are missing

        Example:
            {
                'dates': ['2024-01', '2024-02', '2024-03'],
                'incomes': [3000.0, 3000.0, 3000.0],
                'expenses': [-2000.0, -2000.0, -2000.0]
            }

        Note:
            Expenses are returned as negative values for waterfall chart visualization.
        """
        # Get monthly expense totals from Expenses sheet
        monthly_expenses = self._get_monthly_expenses_totals()
        if monthly_expenses is None or monthly_expenses.empty:
            return {"dates": [], "incomes": [], "expenses": []}

        # Get last 12 months of expense data
        expense_data = monthly_expenses.dropna(subset=[COL_DATE_DT]).iloc[-MONTHS_IN_YEAR:]

        # Calculate monthly incomes for the same months
        incomes = []
        for _idx, row in expense_data.iterrows():
            month_start = row[COL_DATE_DT]
            month_end = month_start
            income = self._get_total_income_for_period(month_start, month_end)
            incomes.append(income)

        return {
            "dates": expense_data[COL_DATE_DT].dt.strftime(DATE_FORMAT_STORAGE).tolist(),
            "incomes": incomes,
            "expenses": [-x for x in expense_data["total_expenses"].tolist()],  # Negative for chart
        }
