"""DataFrame preprocessing utilities for financial data.

This module provides specialized preprocessing functions for financial DataFrames,
handling date parsing, monetary value conversion, and MultiIndex column structures.

Key features:
    - Date column detection and parsing (single and MultiIndex)
    - Monetary value parsing and summation
    - Support for Google Sheets datetime formats
    - Robust error handling with logging

Example:
    >>> from app.logic.dataframe_processor import DataFrameProcessor
    >>> processor = DataFrameProcessor()
    >>> processed_df = processor.preprocess_expenses(expenses_df)
"""

import logging
from typing import Any

import pandas as pd

from app.core.constants import (
    COL_AMOUNT,
    COL_AMOUNT_PARSED,
    COL_DATE,
    COL_DATE_DT,
    DATE_FORMAT_STORAGE,
)
from app.logic.monetary_parsing import parse_monetary_value

logger = logging.getLogger(__name__)


class DataFrameProcessor:
    """Utility class for preprocessing financial DataFrames.

    Provides static methods for preprocessing expenses, assets, liabilities,
    and incomes DataFrames with consistent date parsing and monetary value handling.
    """

    @staticmethod
    def find_date_column(df: pd.DataFrame) -> str | tuple[Any, ...] | None:
        """Find the Date column in a DataFrame, handling both single and MultiIndex columns.

        Searches for a column named exactly "Date" in either single-level or
        MultiIndex column structure.

        Args:
            df: DataFrame to search for Date column

        Returns:
            Column name (str or tuple) if found, None otherwise

        Example:
            >>> df = pd.DataFrame({'Date': ['2024-01'], 'Value': [100]})
            >>> DataFrameProcessor.find_date_column(df)
            'Date'
            >>> df_multi = pd.DataFrame({('Date', ''): ['2024-01'], ('Cash', 'Checking'): [100]})
            >>> DataFrameProcessor.find_date_column(df_multi)
            ('Date', '')
        """
        for col in df.columns:
            if isinstance(col, tuple):
                # MultiIndex column - check if "Date" in either level
                if COL_DATE == col[0] or COL_DATE == col[1]:
                    return col
            else:
                # Single-level column
                if COL_DATE == col:
                    return col
        return None

    @staticmethod
    def sum_monetary_columns_for_row(row: pd.Series, exclude_patterns: list[str]) -> float:
        """Sum all monetary columns in a row, excluding specified patterns.

        Helper method to efficiently sum monetary values in a DataFrame row,
        skipping columns that match exclude patterns (like 'Date', 'date_dt', 'Category').

        Args:
            row: DataFrame row as pandas Series
            exclude_patterns: List of column name patterns to exclude

        Returns:
            Total sum of all monetary values in the row

        Example:
            >>> row = pd.Series({'Date': '2024-01', 'Cash': '1000', 'Stocks': '5000'})
            >>> DataFrameProcessor.sum_monetary_columns_for_row(row, ['Date'])
            6000.0
        """
        total = 0.0
        for col, value in row.items():
            # Skip excluded columns
            skip = False
            for pattern in exclude_patterns:
                if isinstance(col, tuple):
                    # MultiIndex column - check if pattern in either level
                    if pattern in (col[0], col[1]) or pattern in str(col):
                        skip = True
                        break
                else:
                    # Single-level column
                    if col == pattern or pattern in str(col):
                        skip = True
                        break

            if skip:
                continue

            # Parse and add monetary value
            parsed_value = parse_monetary_value(value)
            if parsed_value is not None:
                total += parsed_value

        return total

    @staticmethod
    def preprocess_expenses(expenses_df: pd.DataFrame | None) -> pd.DataFrame | None:
        """Preprocess expenses DataFrame with date and amount parsing.

        Converts Date column to datetime, parses Amount column to float, and sorts by date.

        Args:
            expenses_df: Raw expenses DataFrame

        Returns:
            Preprocessed expenses DataFrame with date_dt and amount_parsed columns,
            or None if no expenses DataFrame was provided
        """
        if expenses_df is None:
            return None

        df = expenses_df.copy()

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

    @staticmethod
    def preprocess_assets(assets_df: pd.DataFrame | None) -> pd.DataFrame | None:
        """Preprocess assets DataFrame with date parsing and sorting.

        Handles both single-level and MultiIndex column structures. Locates the Date
        column dynamically and converts it to datetime for sorting.

        Args:
            assets_df: Raw assets DataFrame

        Returns:
            Preprocessed assets DataFrame with date_dt column, or None if no assets
            DataFrame was provided
        """
        if assets_df is None or assets_df.empty:
            return None

        df = assets_df.copy()

        # Find Date column using helper method
        date_col = DataFrameProcessor.find_date_column(df)

        if date_col is not None:
            df[COL_DATE_DT] = pd.to_datetime(
                df[date_col], format=DATE_FORMAT_STORAGE, errors="coerce"
            )
            df = df.sort_values(by=COL_DATE_DT)

        return df

    @staticmethod
    def preprocess_liabilities(liabilities_df: pd.DataFrame | None) -> pd.DataFrame | None:
        """Preprocess liabilities DataFrame with date parsing and sorting.

        Handles both single-level and MultiIndex column structures. Locates the Date
        column dynamically and converts it to datetime for sorting.

        Args:
            liabilities_df: Raw liabilities DataFrame

        Returns:
            Preprocessed liabilities DataFrame with date_dt column, or None if no
            liabilities DataFrame was provided
        """
        if liabilities_df is None or liabilities_df.empty:
            return None

        df = liabilities_df.copy()

        # Find Date column using helper method
        date_col = DataFrameProcessor.find_date_column(df)

        if date_col is not None:
            df[COL_DATE_DT] = pd.to_datetime(
                df[date_col], format=DATE_FORMAT_STORAGE, errors="coerce"
            )
            df = df.sort_values(by=COL_DATE_DT)

        return df

    @staticmethod
    def preprocess_incomes(incomes_df: pd.DataFrame | None) -> pd.DataFrame | None:
        """Preprocess incomes DataFrame with date parsing and sorting.

        Handles both single-level and MultiIndex column structures. Locates the Date
        column dynamically and converts it to datetime for sorting.

        Args:
            incomes_df: Raw incomes DataFrame

        Returns:
            Preprocessed incomes DataFrame with date_dt column, or None if no
            incomes DataFrame was provided
        """
        if incomes_df is None or incomes_df.empty:
            return None

        df = incomes_df.copy()

        # Find Date column using helper method
        date_col = DataFrameProcessor.find_date_column(df)

        if date_col is not None:
            df[COL_DATE_DT] = pd.to_datetime(
                df[date_col], format=DATE_FORMAT_STORAGE, errors="coerce"
            )
            df = df.sort_values(by=COL_DATE_DT)

        return df
