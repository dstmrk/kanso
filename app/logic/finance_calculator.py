# app/logic/finance_calculator.py
"""Financial calculations with modular architecture.

This module provides the core financial calculation logic for the Kanso application.
It coordinates DataFrame preprocessing and calculations, delegating to specialized
modules for specific concerns.

Key features:
    - Net worth tracking and variation calculations
    - Savings ratio and cash flow analysis
    - Chart data generation for dashboards
    - Modular preprocessing with DataFrameProcessor
    - Multi-currency support via monetary_parsing

Example:
    >>> from app.logic.finance_calculator import FinanceCalculator
    >>> calc = FinanceCalculator(assets_df=assets, liabilities_df=liabilities,
    ...                           expenses_df=expenses, incomes_df=incomes)
    >>> calc.get_current_net_worth()
    50000.0
"""

import logging
from typing import Any

import pandas as pd

from app.core.constants import (
    CATEGORY_ASSETS,
    CATEGORY_EXPENSES,
    CATEGORY_LIABILITIES,
    CATEGORY_SAVINGS,
    COL_AMOUNT_PARSED,
    COL_CATEGORY,
    COL_DATE,
    COL_DATE_DT,
    COL_MERCHANT,
    COL_NET_WORTH_PARSED,
    COL_TYPE,
    DATE_FORMAT_DISPLAY,
    DATE_FORMAT_STORAGE,
    MONTHS_IN_YEAR,
    MONTHS_LOOKBACK_YEAR,
)
from app.core.monitoring import track_performance
from app.logic.dataframe_processor import DataFrameProcessor, is_date_column
from app.logic.monetary_parsing import parse_monetary_value

logger = logging.getLogger(__name__)


class FinanceCalculator:
    """Optimized finance calculator with cached DataFrame preprocessing.

    This class provides comprehensive financial calculations including net worth tracking,
    savings ratios, cash flow analysis, and asset/liability breakdowns. It uses lazy
    preprocessing and caching to avoid redundant pandas operations.

    The calculator expects monthly financial data with dates in YYYY-MM format and
    supports multiple currency formats for monetary values.

    Attributes:
        assets_df: Optional assets breakdown DataFrame (supports MultiIndex)
        liabilities_df: Optional liabilities breakdown DataFrame (supports MultiIndex)
        expenses_df: Optional expenses breakdown DataFrame
        incomes_df: Optional incomes breakdown DataFrame (supports MultiIndex)

    Note:
        Net Worth is calculated dynamically from Assets and Liabilities sheets.

    Example:
        >>> assets_df = pd.DataFrame({
        ...     'Date': ['2024-01', '2024-02'],
        ...     'Cash': ['€ 5.000', '€ 6.000'],
        ...     'Stocks': ['€ 10.000', '€ 11.000']
        ... })
        >>> liabilities_df = pd.DataFrame({
        ...     'Date': ['2024-01', '2024-02'],
        ...     'Mortgage': ['€ 100.000', '€ 99.000']
        ... })
        >>> calc = FinanceCalculator(assets_df=assets_df, liabilities_df=liabilities_df)
        >>> calc.get_current_net_worth()  # (6000 + 11000) - 99000 = -82000
        -82000.0
    """

    def __init__(
        self,
        assets_df: pd.DataFrame | None = None,
        liabilities_df: pd.DataFrame | None = None,
        expenses_df: pd.DataFrame | None = None,
        incomes_df: pd.DataFrame | None = None,
    ) -> None:
        """Initialize the calculator with financial data.

        Args:
            assets_df: DataFrame with detailed asset breakdown (supports MultiIndex)
            liabilities_df: DataFrame with detailed liability breakdown (supports MultiIndex)
            expenses_df: DataFrame with Month, Category, and Amount columns
            incomes_df: DataFrame with detailed income breakdown (supports MultiIndex)

        Note:
            Net Worth is calculated from Assets and Liabilities sheets.
            DataFrames are not processed immediately. Processing happens lazily when
            data is first accessed through properties.
        """
        self.expenses_df = expenses_df
        self.assets_df = assets_df
        self.liabilities_df = liabilities_df
        self.incomes_df = incomes_df
        self._processed_expenses_df = None
        self._processed_assets_df = None
        self._processed_liabilities_df = None
        self._processed_incomes_df = None
        self._net_worth_df = None

    @property
    def processed_expenses_df(self) -> pd.DataFrame | None:
        """Lazily processed and cached expenses DataFrame."""
        if self.expenses_df is not None and self._processed_expenses_df is None:
            self._processed_expenses_df = DataFrameProcessor.preprocess_expenses(self.expenses_df)
        return self._processed_expenses_df

    @property
    def processed_assets_df(self) -> pd.DataFrame | None:
        """Lazily processed and cached assets DataFrame."""
        if self.assets_df is not None and self._processed_assets_df is None:
            self._processed_assets_df = DataFrameProcessor.preprocess_assets(self.assets_df)
        return self._processed_assets_df

    @property
    def processed_liabilities_df(self) -> pd.DataFrame | None:
        """Lazily processed and cached liabilities DataFrame."""
        if self.liabilities_df is not None and self._processed_liabilities_df is None:
            self._processed_liabilities_df = DataFrameProcessor.preprocess_liabilities(
                self.liabilities_df
            )
        return self._processed_liabilities_df

    @property
    def processed_incomes_df(self) -> pd.DataFrame | None:
        """Lazily processed and cached incomes DataFrame."""
        if self.incomes_df is not None and self._processed_incomes_df is None:
            self._processed_incomes_df = DataFrameProcessor.preprocess_incomes(self.incomes_df)
        return self._processed_incomes_df

    @property
    def net_worth_df(self) -> pd.DataFrame:
        """Lazily calculated and cached Net Worth DataFrame.

        Calculates monthly Net Worth from Assets and Liabilities sheets.

        Returns:
            DataFrame with columns: date_dt, net_worth_parsed
            Returns empty DataFrame if Assets and Liabilities are not available
        """
        if self._net_worth_df is None:
            # Calculate from Assets and Liabilities
            self._net_worth_df = self._calculate_net_worth_from_assets_liabilities()

        return self._net_worth_df

    def _get_monthly_expenses_totals(self) -> pd.DataFrame | None:
        """Calculate monthly expense totals from detailed Expenses sheet.

        Aggregates all expense transactions by month, summing amounts to get
        monthly totals from the Expenses sheet.

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

    @staticmethod
    def _sum_monetary_by_date(
        df: pd.DataFrame, exclude_cols: list[str]
    ) -> dict[pd.Timestamp, float]:
        """Group a preprocessed DataFrame by date and sum all monetary columns per date."""
        result: dict[pd.Timestamp, float] = {}
        for date, group in df.groupby(COL_DATE_DT):
            if isinstance(date, pd.Series):
                date = date.iloc[0]
            row = group.iloc[0]
            result[date] = DataFrameProcessor.sum_monetary_columns_for_row(row, exclude_cols)
        return result

    def _calculate_net_worth_from_assets_liabilities(self) -> pd.DataFrame:
        """Calculate monthly Net Worth from Assets and Liabilities sheets.

        Combines Assets and Liabilities data to compute Net Worth for each month:
        Net Worth = Total Assets - |Total Liabilities|

        Note:
            - Liabilities are always subtracted using their absolute value, regardless
              of whether they're stored as positive or negative in the sheet
            - Net worth is only calculated for dates present in the Incomes sheet
              (if Incomes sheet is available). This ensures we only show financial
              data for periods where we have complete income information.
            - Uses vectorized operations for better performance on large datasets

        Returns:
            DataFrame with columns: date_dt (datetime), net_worth_parsed (float)
            Returns empty DataFrame if neither assets_df nor liabilities_df are available

        Example:
            >>> calc = FinanceCalculator(None, assets_df=assets, liabilities_df=liabilities)
            >>> nw_df = calc._calculate_net_worth_from_assets_liabilities()
            >>> nw_df.columns
            Index(['date_dt', 'net_worth_parsed'], dtype='object')
        """
        assets_df = self.processed_assets_df
        liabilities_df = self.processed_liabilities_df
        incomes_df = self.processed_incomes_df

        # If neither sheet is available, return empty DataFrame
        if (assets_df is None or assets_df.empty) and (
            liabilities_df is None or liabilities_df.empty
        ):
            return pd.DataFrame(columns=[COL_DATE_DT, COL_NET_WORTH_PARSED])

        # Get max date from Incomes sheet to limit net worth calculation
        max_income_date = None
        if incomes_df is not None and not incomes_df.empty and COL_DATE_DT in incomes_df.columns:
            max_income_date = incomes_df[COL_DATE_DT].max()

        # Columns to exclude when summing monetary values
        exclude_date_cols = [COL_DATE, COL_DATE_DT, "date_dt"]
        exclude_liability_cols = exclude_date_cols + [COL_CATEGORY]

        assets_by_date: dict[pd.Timestamp, float] = (
            self._sum_monetary_by_date(assets_df, exclude_date_cols)
            if assets_df is not None and not assets_df.empty
            else {}
        )
        liabilities_by_date: dict[pd.Timestamp, float] = (
            self._sum_monetary_by_date(liabilities_df, exclude_liability_cols)
            if liabilities_df is not None and not liabilities_df.empty
            else {}
        )

        # Get all unique dates
        all_dates = set(assets_by_date.keys()) | set(liabilities_by_date.keys())

        # Filter dates to only include those up to max income date
        if max_income_date is not None:
            valid_dates = {date for date in all_dates if date <= max_income_date}
        else:
            valid_dates = all_dates

        # Calculate Net Worth for each valid date
        net_worth_data = []
        for date in sorted(valid_dates):
            assets_total = assets_by_date.get(date, 0.0)
            liabilities_total = liabilities_by_date.get(date, 0.0)
            # Use abs() to handle both positive and negative liability formats
            net_worth = assets_total - abs(liabilities_total)
            net_worth_data.append({COL_DATE_DT: date, COL_NET_WORTH_PARSED: net_worth})

        return pd.DataFrame(net_worth_data)

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
            If no incomes_df is provided, this method returns 0.0.
        """
        # Return 0 if no incomes_df available
        if self.processed_incomes_df is None:
            return 0.0

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
            # Skip date columns (Date, date_dt, and variants)
            if is_date_column(col):
                continue

            # Sum all monetary columns
            try:
                total += float(df[col].apply(parse_monetary_value).sum())
            except Exception as e:
                logger.warning(f"Failed to parse income column '{col}': {e}")
                continue

        return total

    @staticmethod
    def _extract_source_name(col: Any) -> str:
        """Extract a meaningful source name from a column key (str or tuple).

        For tuple columns (MultiIndex), filters out empty parts, monetary values,
        and pure numbers, returning the last meaningful text part.
        """
        if not isinstance(col, tuple):
            return str(col)

        meaningful_parts = []
        for part in col:
            part_str = str(part).strip()
            if not part_str:
                continue
            # Skip if it parses as a non-zero monetary value
            try:
                parsed = parse_monetary_value(part_str)
                if parsed is not None and parsed != 0:
                    continue
            except Exception:
                pass
            # Skip pure numbers or date-like strings
            test_str = part_str.replace(".", "").replace(",", "").replace("-", "")
            if test_str.isdigit():
                continue
            meaningful_parts.append(part_str)

        return meaningful_parts[-1] if meaningful_parts else "Income"

    def _get_income_sources_for_period(
        self, start_date: pd.Timestamp | None = None, end_date: pd.Timestamp | None = None
    ) -> dict[str, float]:
        """Get breakdown of income by source for a specific period.

        Returns a dictionary with income sources as keys and their totals as values.
        If incomes_df has multiple sources (multi-index), each source is separated.
        If there's only one source or using fallback Income column, returns single "Income" entry.

        Args:
            start_date: Optional start date for filtering (inclusive)
            end_date: Optional end date for filtering (inclusive)

        Returns:
            Dictionary mapping income source names to their total amounts

        Example:
            {'Salary': 30000.0, 'Freelance': 5000.0, 'Investments': 2000.0}
            or
            {'Income': 37000.0}  # Single source or fallback
        """
        # Return empty dict if no incomes_df available
        if self.processed_incomes_df is None:
            return {}

        # Use incomes_df - get income sources separately
        df = self.processed_incomes_df

        # Filter by date range if specified
        if COL_DATE_DT in df.columns:
            if start_date is not None:
                df = df[df[COL_DATE_DT] >= start_date]
            if end_date is not None:
                df = df[df[COL_DATE_DT] <= end_date]

        # Calculate income by source
        income_sources: dict[str, float] = {}

        for col in df.columns:
            if is_date_column(col):
                continue

            try:
                source_name = self._extract_source_name(col)
                amount = float(df[col].apply(parse_monetary_value).sum())

                if source_name in income_sources:
                    income_sources[source_name] += amount
                else:
                    income_sources[source_name] = amount

            except Exception as e:
                logger.warning(f"Failed to parse income source column '{col}': {e}")
                continue

        return income_sources

    def get_current_net_worth(self) -> float:
        """Get the most recent net worth value.

        Calculates Net Worth from Assets and Liabilities sheets.

        Returns:
            Current net worth as float, or 0.0 if no data available
        """
        nw_df = self.net_worth_df
        if nw_df.empty:
            return 0.0
        return float(nw_df[COL_NET_WORTH_PARSED].iloc[-1])

    def get_last_update_date(self) -> str:
        """Get the date of the last update.

        Returns latest date from any available sheet (Assets, Liabilities, Incomes, Expenses).

        Returns:
            Date string in MM-YYYY format (e.g., "01-2025"), or empty string if no data
        """
        nw_df = self.net_worth_df
        if nw_df.empty:
            return ""
        return nw_df[COL_DATE_DT].iloc[-1].strftime(DATE_FORMAT_DISPLAY)

    def get_month_over_month_net_worth_variation_percentage(self) -> float:
        """Get month-over-month net worth percentage change.

        Calculates the relative change between the last two months from Assets/Liabilities.

        Returns:
            Percentage change as decimal (e.g., 0.05 for 5% increase),
            or 0.0 if insufficient data

        Example:
            If net worth went from €20,000 to €21,000, returns 0.05 (5% increase)
        """
        nw_df = self.net_worth_df
        if len(nw_df) < 2:
            return 0.0

        current: float = float(nw_df[COL_NET_WORTH_PARSED].iloc[-1])
        previous: float = float(nw_df[COL_NET_WORTH_PARSED].iloc[-2])

        return (current - previous) / previous if previous != 0 else 0.0

    def get_month_over_month_net_worth_variation_absolute(self) -> float:
        """Get month-over-month net worth absolute change.

        Calculates the absolute difference between the last two months from Assets/Liabilities.

        Returns:
            Absolute change in currency units (e.g., 1000.0 for €1,000 increase),
            or 0.0 if insufficient data

        Example:
            If net worth went from €20,000 to €21,000, returns 1000.0
        """
        nw_df = self.net_worth_df
        if len(nw_df) < 2:
            return 0.0

        return float(nw_df[COL_NET_WORTH_PARSED].iloc[-1] - nw_df[COL_NET_WORTH_PARSED].iloc[-2])

    def get_year_over_year_net_worth_variation_percentage(self) -> float:
        """Get year-over-year net worth percentage change.

        Compares current net worth with the value from 13 months ago (calculated from Assets/Liabilities).

        Returns:
            Percentage change as decimal (e.g., 1.2 for 120% increase),
            or 0.0 if insufficient data (less than 13 months)

        Example:
            If net worth went from €10,000 to €22,000, returns 1.2 (120% increase)
        """
        nw_df = self.net_worth_df
        if len(nw_df) < MONTHS_LOOKBACK_YEAR:
            return 0.0

        current: float = float(nw_df[COL_NET_WORTH_PARSED].iloc[-1])
        previous_year: float = float(nw_df[COL_NET_WORTH_PARSED].iloc[-MONTHS_LOOKBACK_YEAR])

        return (current - previous_year) / previous_year if previous_year != 0 else 0.0

    def get_year_over_year_net_worth_variation_absolute(self) -> float:
        """Get year-over-year net worth absolute change.

        Compares current net worth with the value from 13 months ago (calculated from Assets/Liabilities).

        Returns:
            Absolute change in currency units (e.g., 12000.0 for €12,000 increase),
            or 0.0 if insufficient data (less than 13 months)

        Example:
            If net worth went from €10,000 to €22,000, returns 12000.0
        """
        nw_df = self.net_worth_df
        if len(nw_df) < MONTHS_LOOKBACK_YEAR:
            return 0.0

        return float(
            nw_df[COL_NET_WORTH_PARSED].iloc[-1]
            - nw_df[COL_NET_WORTH_PARSED].iloc[-MONTHS_LOOKBACK_YEAR]
        )

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
        expenses: float = float(expenses_last_12["total_expenses"].sum())

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
        expenses: float = float(expenses_last_12["total_expenses"].sum())

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
    def get_monthly_net_worth(self) -> dict[str, list[Any]]:
        """Get monthly net worth data for charting.

        Calculates Net Worth from Assets and Liabilities sheets.

        Returns:
            Dictionary with 'dates' (list of YYYY-MM strings) and 'values' (list of floats),
            or empty lists if no data available

        Example:
            {
                'dates': ['2024-01', '2024-02', '2024-03'],
                'values': [10000.0, 11000.0, 12000.0]
            }
        """
        nw_df = self.net_worth_df
        if nw_df.empty:
            return {"dates": [], "values": []}

        df = nw_df.dropna(subset=[COL_DATE_DT])
        return {
            "dates": df[COL_DATE_DT].dt.strftime(DATE_FORMAT_STORAGE).tolist(),
            "values": [float(v) for v in df[COL_NET_WORTH_PARSED].tolist()],
        }

    @staticmethod
    def _lookup_date_rows(
        df_filtered: pd.DataFrame, dates: list[str]
    ) -> dict[str, pd.Series | None]:
        """Pre-compute a mapping from date string to the first matching row (or None)."""
        date_rows: dict[str, pd.Series | None] = {}
        for date in dates:
            rows = df_filtered[
                df_filtered[COL_DATE_DT].dt.strftime(DATE_FORMAT_STORAGE) == date
            ]
            date_rows[date] = rows.iloc[0] if not rows.empty else None
        return date_rows

    @staticmethod
    def _apply_negate(value: float, negate: bool) -> float:
        """Return negated value if negate is True."""
        return -value if negate else value

    @staticmethod
    def _add_multiindex_col(
        classes: dict[str, list[float]],
        col: tuple[str, str],
        dates: list[str],
        date_rows: dict[str, pd.Series | None],
        skip_cols: set[str],
        negate: bool,
    ) -> None:
        """Process a MultiIndex column, aggregating values into its category series."""
        category = col[0].strip()
        if not category or category in skip_cols:
            return
        if category not in classes:
            classes[category] = [0.0] * len(dates)
        for i, date in enumerate(dates):
            row = date_rows[date]
            if row is not None:
                value = parse_monetary_value(row[col])
                classes[category][i] += FinanceCalculator._apply_negate(value, negate)

    @staticmethod
    def _add_single_col(
        classes: dict[str, list[float]],
        col: str,
        dates: list[str],
        date_rows: dict[str, pd.Series | None],
        skip_cols: set[str],
        negate: bool,
    ) -> None:
        """Process a single-index column, creating its own series."""
        item = str(col)
        if item in (COL_DATE, COL_CATEGORY) or item in skip_cols:
            return
        series: list[float] = []
        for date in dates:
            row = date_rows[date]
            if row is not None:
                value = parse_monetary_value(row[col])
                series.append(FinanceCalculator._apply_negate(value, negate))
            else:
                series.append(0.0)
        classes[item] = series

    @staticmethod
    def _build_class_series(
        df: pd.DataFrame,
        dates: list[str],
        negate: bool = False,
        extra_skip_cols: list[str] | None = None,
    ) -> dict[str, list[float]]:
        """Build time-series data grouped by column category from a financial DataFrame.

        For MultiIndex columns, aggregates by the first level (category).
        For single-index columns, each column becomes its own series.

        Args:
            df: Preprocessed DataFrame with COL_DATE_DT column.
            dates: List of YYYY-MM date strings defining the time series.
            negate: If True, negate all values (used for liabilities).
            extra_skip_cols: Additional column names to skip beyond date columns.
        """
        skip_cols = set(extra_skip_cols or [])
        df_filtered = df[df[COL_DATE_DT].dt.strftime(DATE_FORMAT_STORAGE).isin(dates)]
        date_rows = FinanceCalculator._lookup_date_rows(df_filtered, dates)
        columns = [col for col in df.columns if not is_date_column(col)]

        classes: dict[str, list[float]] = {}
        for col in columns:
            if isinstance(col, tuple) and len(col) == 2:
                FinanceCalculator._add_multiindex_col(
                    classes, col, dates, date_rows, skip_cols, negate
                )
            else:
                FinanceCalculator._add_single_col(
                    classes, col, dates, date_rows, skip_cols, negate
                )

        return classes

    @track_performance("get_monthly_net_worth_by_asset_class")
    def get_monthly_net_worth_by_asset_class(self) -> dict[str, Any]:
        """Get monthly net worth evolution broken down by asset and liability classes.

        Returns time series data for each asset class (positive values) and liability
        class (negative values), plus the total net worth line.

        Returns:
            Dictionary with:
                - dates: List of YYYY-MM strings
                - total: List of total net worth values
                - asset_classes: Dict of {class_name: [values]} for assets (positive)
                - liability_classes: Dict of {class_name: [values]} for liabilities (negative)

        Example (single-index):
            {
                'dates': ['2024-01', '2024-02'],
                'total': [32000.0, 33500.0],
                'asset_classes': {
                    'Checking': [2000.0, 2500.0],
                    'Savings': [10000.0, 11000.0]
                },
                'liability_classes': {
                    'Mortgage': [-200000.0, -199000.0],
                    'Car Loan': [-15000.0, -14500.0]
                }
            }

        Example (multi-index):
            {
                'dates': ['2024-01', '2024-02'],
                'total': [32000.0, 33500.0],
                'asset_classes': {
                    'Cash': [12000.0, 13500.0],  # Sum of Checking + Savings
                    'Investments': [20000.0, 20000.0]  # Sum of Stocks + Bonds
                },
                'liability_classes': {
                    'Loans': [-215000.0, -213500.0]  # Sum of Mortgage + Car Loan
                }
            }
        """
        # Get net worth for dates and total values
        nw_data = self.get_monthly_net_worth()
        if not nw_data["dates"]:
            return {
                "dates": [],
                "total": [],
                "asset_classes": {},
                "liability_classes": {},
            }

        dates = nw_data["dates"]
        total = nw_data["values"]

        assets_df = self.processed_assets_df
        liabilities_df = self.processed_liabilities_df

        asset_classes: dict[str, list[float]] = (
            self._build_class_series(assets_df, dates, extra_skip_cols=[COL_CATEGORY])
            if assets_df is not None and not assets_df.empty
            else {}
        )
        liability_classes: dict[str, list[float]] = (
            self._build_class_series(
                liabilities_df, dates, negate=True, extra_skip_cols=[COL_CATEGORY]
            )
            if liabilities_df is not None and not liabilities_df.empty
            else {}
        )

        return {
            "dates": dates,
            "total": total,
            "asset_classes": asset_classes,
            "liability_classes": liability_classes,
        }

    @staticmethod
    def _should_skip_column(
        col: Any, skip_category: bool
    ) -> bool:
        """Check if a column should be skipped during value extraction."""
        if is_date_column(col):
            return True
        if not skip_category:
            return False
        return col == COL_CATEGORY or (isinstance(col, tuple) and COL_CATEGORY in col)

    @staticmethod
    def _extract_multiindex_value(
        result: dict[str, Any],
        col: tuple[str, str],
        row: pd.Series,
        skip_category: bool,
    ) -> None:
        """Extract a value from a MultiIndex column into the result dict."""
        category, item = col[0].strip(), col[1].strip()
        if not category or (skip_category and category == COL_CATEGORY):
            return
        value = parse_monetary_value(row[col])
        if category not in result:
            result[category] = {}
        result[category][item] = value

    @staticmethod
    def _extract_values_from_row(
        df: pd.DataFrame,
        row: pd.Series,
        skip_category: bool = False,
    ) -> dict[str, Any]:
        """Extract monetary values from a DataFrame row, grouped by column structure.

        For MultiIndex columns, groups values under their category (first level).
        For single-index columns, maps column name directly to value.
        """
        result: dict[str, Any] = {}
        for col in df.columns:
            if FinanceCalculator._should_skip_column(col, skip_category):
                continue
            if isinstance(col, tuple) and len(col) == 2:
                FinanceCalculator._extract_multiindex_value(result, col, row, skip_category)
            else:
                result[col] = parse_monetary_value(row[col])
        return result

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
        assets_df = self.processed_assets_df
        liabilities_df = self.processed_liabilities_df

        # Extract asset values from latest row
        asset_values: dict[str, Any] = {}
        reference_date = None
        if assets_df is not None and not assets_df.empty:
            reference_date = assets_df[COL_DATE_DT].iloc[-1]
            asset_values = self._extract_values_from_row(assets_df, assets_df.iloc[-1])

        # Find matching liability row (by reference date from assets)
        liability_values: dict[str, Any] = {}
        if liabilities_df is not None and not liabilities_df.empty:
            if reference_date is not None:
                matching_rows = liabilities_df[liabilities_df[COL_DATE_DT] <= reference_date]
                latest_row = (
                    matching_rows.iloc[-1] if not matching_rows.empty else liabilities_df.iloc[-1]
                )
            else:
                latest_row = liabilities_df.iloc[-1]
            liability_values = self._extract_values_from_row(
                liabilities_df, latest_row, skip_category=True
            )

        return {
            CATEGORY_ASSETS: asset_values,
            CATEGORY_LIABILITIES: liability_values,
        }

    @track_performance("get_cash_flow_last_12_months")
    def get_cash_flow_last_12_months(self) -> dict[str, float]:
        """Get cash flow data for last 12 months with income source breakdown.

        Calculates total income (by source), total expenses, and savings for the last 12 months.
        Also includes breakdown by expense categories if expenses_df is available.
        Uses incomes_df if available, otherwise falls back to Income column from main DataFrame.

        Returns:
            Dictionary with income sources, 'Savings', 'Expenses', and category keys

        Example with multiple income sources:
            {
                'Salary': 30000.0,
                'Freelance': 5000.0,
                'Investments': 2000.0,
                'Savings': 12000.0,
                'Expenses': 24000.0,
                'Food': 6000.0,
                'Transport': 3000.0,
                'Housing': 15000.0
            }

        Example with single income source:
            {
                'Income': 36000.0,
                'Savings': 12000.0,
                'Expenses': 24000.0,
                'Food': 6000.0,
                ...
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
        total_expenses: float = float(ef_last_12[COL_AMOUNT_PARSED].sum())

        # Income by source (multiple sources or single)
        income_sources = self._get_income_sources_for_period(start_date, latest_date)
        total_income = sum(income_sources.values())

        # Expenses by category - convert numpy scalars to float
        expenses_by_category: dict[str, float] = {
            k: float(v)
            for k, v in ef_last_12.groupby(COL_CATEGORY)[COL_AMOUNT_PARSED].sum().to_dict().items()
        }

        # Build result with income sources first
        result: dict[str, float] = {}
        result.update(income_sources)  # Add all income sources
        result[CATEGORY_EXPENSES] = total_expenses
        result[CATEGORY_SAVINGS] = total_income - total_expenses
        result.update(expenses_by_category)  # Add expense categories

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
        # Convert numpy scalars to float
        return {
            k: float(v)
            for k, v in ef_last_12.groupby(COL_CATEGORY)[COL_AMOUNT_PARSED].sum().to_dict().items()
        }

    @track_performance("get_expenses_by_merchant_last_12_months")
    def get_expenses_by_merchant_last_12_months(
        self, cumulative_threshold: float = 0.8
    ) -> dict[str, float]:
        """Get expenses by merchant for last 12 months, showing merchants up to threshold.

        Uses a cumulative threshold approach: shows individual merchants until their
        cumulative sum reaches the specified percentage of total expenses. This adapts
        to data distribution - showing more merchants when expenses are spread out,
        and fewer when concentrated.

        Args:
            cumulative_threshold: Cumulative percentage threshold (default 0.8 = 80%)

        Returns:
            Dictionary mapping merchant names to total expense amounts.
            Merchants up to cumulative threshold shown individually, rest as "Other".
            Empty dict if expenses_df is not available or COL_MERCHANT not present.

        Example:
            {'Amazon': 2000.0, 'Grocery Store': 1500.0, ..., 'Other': 500.0}
        """
        if (
            self.processed_expenses_df is None
            or COL_MERCHANT not in self.processed_expenses_df.columns
        ):
            return {}

        ef: pd.DataFrame = self.processed_expenses_df
        latest_date: pd.Timestamp = ef[COL_DATE_DT].max()
        start_date: pd.Timestamp = (latest_date - pd.DateOffset(months=MONTHS_IN_YEAR - 1)).replace(
            day=1
        )

        ef_last_12: pd.DataFrame = ef[
            (ef[COL_DATE_DT] >= start_date) & (ef[COL_DATE_DT] <= latest_date)
        ]

        # Group by merchant and sum
        merchant_totals = (
            ef_last_12.groupby(COL_MERCHANT)[COL_AMOUNT_PARSED].sum().sort_values(ascending=False)
        )

        # Calculate cumulative threshold
        total_expenses = merchant_totals.sum()
        threshold_amount = total_expenses * cumulative_threshold
        cumulative_sum = 0.0

        result: dict[str, float] = {}
        other_total = 0.0

        for merchant, amount in merchant_totals.items():
            if cumulative_sum < threshold_amount:
                result[merchant] = float(amount)
                cumulative_sum += amount
            else:
                other_total += amount

        # Add "Other" category if there are remaining expenses
        if other_total > 0:
            result["Other"] = float(other_total)

        return result

    @track_performance("get_expenses_by_type_last_12_months")
    def get_expenses_by_type_last_12_months(self) -> dict[str, float]:
        """Get expenses by type for last 12 months.

        Returns:
            Dictionary mapping type names to total expense amounts,
            or empty dict if expenses_df is not available or COL_TYPE not present

        Example:
            {'Fixed': 15000.0, 'Variable': 9000.0, 'One-time': 2000.0}
        """
        if self.processed_expenses_df is None or COL_TYPE not in self.processed_expenses_df.columns:
            return {}

        ef: pd.DataFrame = self.processed_expenses_df
        latest_date: pd.Timestamp = ef[COL_DATE_DT].max()
        start_date: pd.Timestamp = (latest_date - pd.DateOffset(months=MONTHS_IN_YEAR - 1)).replace(
            day=1
        )

        ef_last_12: pd.DataFrame = ef[
            (ef[COL_DATE_DT] >= start_date) & (ef[COL_DATE_DT] <= latest_date)
        ]

        # Convert numpy scalars to float
        return {
            k: float(v)
            for k, v in ef_last_12.groupby(COL_TYPE)[COL_AMOUNT_PARSED].sum().to_dict().items()
        }

    @track_performance("get_incomes_vs_expenses")
    def get_incomes_vs_expenses(self) -> dict[str, list[Any]]:
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

    @staticmethod
    def _build_cumulative_by_month(
        year_data: pd.DataFrame, last_valid_month: int | None = None
    ) -> list[float | None]:
        """Build cumulative expense totals for each month of a year.

        Args:
            year_data: Expense data filtered to a single year.
            last_valid_month: If set, months beyond this are returned as None.
        """
        result: list[float | None] = []
        for month in range(1, 13):
            month_data = year_data[year_data[COL_DATE_DT].dt.month <= month]
            cumulative = month_data["total_expenses"].sum() if not month_data.empty else 0.0
            if last_valid_month is not None and month > last_valid_month:
                result.append(None)
            else:
                result.append(cumulative)
        return result

    @staticmethod
    def _build_projection(
        monthly_expenses: pd.DataFrame,
        current_cumulative: list[float | None],
        last_valid_month: int,
    ) -> list[float | None]:
        """Project future months based on average monthly expenses."""
        projected: list[float | None] = [None] * 12
        if last_valid_month >= 12 or last_valid_month == 0:
            return projected

        last_12 = monthly_expenses.iloc[-MONTHS_IN_YEAR:]
        avg = last_12["total_expenses"].mean() if not last_12.empty else 0.0
        base = current_cumulative[last_valid_month - 1]
        if base is None:
            return projected

        for month in range(last_valid_month + 1, 13):
            projected[month - 1] = base + (avg * (month - last_valid_month))
        return projected

    @track_performance("get_expenses_yoy_comparison")
    def get_expenses_yoy_comparison(self) -> dict[str, Any]:
        """Get year-over-year expenses comparison (cumulative by month).

        Compares current year spending vs previous year on a month-by-month cumulative basis.

        Returns:
            Dictionary with:
                - months: List of month labels (Jan, Feb, Mar, ...)
                - current_year: List of cumulative expenses for current year
                - previous_year: List of cumulative expenses for previous year
                - current_year_label: Year label (e.g., "2025")
                - previous_year_label: Year label (e.g., "2024")

        Example:
            {
                'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                'current_year': [1000.0, 2200.0, 3500.0, 4800.0, 6100.0, 7400.0, 0, 0, 0, 0, 0, 0],
                'previous_year': [950.0, 2100.0, 3400.0, 4700.0, 6000.0, 7300.0, 8600.0, 9900.0, 11200.0, 12500.0, 13800.0, 15100.0],
                'current_year_label': '2025',
                'previous_year_label': '2024'
            }
        """
        # Get monthly expense totals
        monthly_expenses = self._get_monthly_expenses_totals()
        if monthly_expenses is None or monthly_expenses.empty:
            return {
                "months": [],
                "current_year": [],
                "previous_year": [],
                "current_year_label": "",
                "previous_year_label": "",
            }

        # Get current year and previous year
        latest_date = monthly_expenses[COL_DATE_DT].max()
        current_year = latest_date.year
        previous_year = current_year - 1

        # Month labels
        month_labels = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]

        # Filter data for current and previous year
        current_year_data = monthly_expenses[monthly_expenses[COL_DATE_DT].dt.year == current_year]
        previous_year_data = monthly_expenses[
            monthly_expenses[COL_DATE_DT].dt.year == previous_year
        ]

        last_valid_month = (
            int(current_year_data[COL_DATE_DT].dt.month.max()) if not current_year_data.empty else 0
        )

        current_year_cumulative = self._build_cumulative_by_month(
            current_year_data, last_valid_month
        )
        previous_year_cumulative = self._build_cumulative_by_month(previous_year_data)

        current_year_projected = self._build_projection(
            monthly_expenses, current_year_cumulative, last_valid_month
        )

        return {
            "months": month_labels,
            "current_year": current_year_cumulative,
            "current_year_projected": current_year_projected,
            "previous_year": previous_year_cumulative,
            "current_year_label": str(current_year),
            "previous_year_label": str(previous_year),
            "last_valid_month": last_valid_month,
        }

    def get_unique_expense_fields(self) -> dict[str, list[str]]:
        """Get unique values for expense fields (merchants, categories, types).

        Extracts unique, non-null values from the expenses DataFrame for use
        in autocomplete fields and dropdowns.

        Returns:
            Dictionary with keys 'merchants', 'categories', 'types', each containing
            a sorted list of unique values. Returns empty lists if no data available.

        Example:
            {
                'merchants': ['Amazon', 'Grocery Store', 'Netflix'],
                'categories': ['Entertainment', 'Food', 'Subscriptions'],
                'types': ['Essential', 'Discretionary']
            }
        """
        if self.processed_expenses_df is None or self.processed_expenses_df.empty:
            return {"merchants": [], "categories": [], "types": []}

        df = self.processed_expenses_df

        # Extract unique values and sort alphabetically
        merchants = (
            sorted(df[COL_MERCHANT].dropna().unique().tolist())
            if COL_MERCHANT in df.columns
            else []
        )
        categories = (
            sorted(df[COL_CATEGORY].dropna().unique().tolist())
            if COL_CATEGORY in df.columns
            else []
        )
        types = sorted(df[COL_TYPE].dropna().unique().tolist()) if COL_TYPE in df.columns else []

        return {
            "merchants": merchants,
            "categories": categories,
            "types": types,
        }

    def get_filtered_assets_liabilities(
        self,
    ) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
        """Get assets and liabilities DataFrames filtered to valid dates.

        Filters DataFrames to only include dates that have corresponding entries
        in the net worth calculation (i.e., dates up to max income date).

        Returns:
            Tuple of (filtered_assets_df, filtered_liabilities_df).
            Either can be None if no data available.

        Example:
            >>> calc = FinanceCalculator(assets_df=assets, liabilities_df=liabilities)
            >>> assets, liabilities = calc.get_filtered_assets_liabilities()
        """
        # Get valid dates from net worth calculation
        nw_data = self.get_monthly_net_worth()
        valid_dates = nw_data.get("dates", [])

        if not valid_dates:
            return None, None

        # Filter assets to valid dates
        filtered_assets = None
        if self.processed_assets_df is not None and not self.processed_assets_df.empty:
            filtered_assets = self.processed_assets_df[
                self.processed_assets_df[COL_DATE_DT]
                .dt.strftime(DATE_FORMAT_STORAGE)
                .isin(valid_dates)
            ].copy()

        # Filter liabilities to valid dates
        filtered_liabilities = None
        if self.processed_liabilities_df is not None and not self.processed_liabilities_df.empty:
            filtered_liabilities = self.processed_liabilities_df[
                self.processed_liabilities_df[COL_DATE_DT]
                .dt.strftime(DATE_FORMAT_STORAGE)
                .isin(valid_dates)
            ].copy()

        return filtered_assets, filtered_liabilities
