"""Unit tests for DataFrame preprocessing utilities.

Tests the dataframe_processor module's preprocessing functions for expenses,
assets, liabilities, and incomes DataFrames with various column structures.
"""

import pandas as pd
import pytest

from app.core.constants import COL_AMOUNT_PARSED, COL_DATE_DT
from app.logic.dataframe_processor import DataFrameProcessor


class TestFindDateColumn:
    """Tests for finding Date column in various DataFrame structures."""

    def test_find_date_single_level(self):
        """Test finding Date in single-level columns."""
        df = pd.DataFrame({"Date": ["2024-01"], "Value": [100]})
        assert DataFrameProcessor.find_date_column(df) == "Date"

    def test_find_date_multiindex_first_level(self):
        """Test finding Date in MultiIndex columns (first level)."""
        df = pd.DataFrame({("Date", ""): ["2024-01"], ("Cash", "Checking"): [100]})
        result = DataFrameProcessor.find_date_column(df)
        assert result == ("Date", "")

    def test_find_date_multiindex_second_level(self):
        """Test finding Date in MultiIndex columns (second level)."""
        df = pd.DataFrame({("", "Date"): ["2024-01"], ("Assets", "Cash"): [100]})
        result = DataFrameProcessor.find_date_column(df)
        assert result == ("", "Date")

    def test_find_date_not_found(self):
        """Test when Date column doesn't exist."""
        df = pd.DataFrame({"Month": ["2024-01"], "Value": [100]})
        assert DataFrameProcessor.find_date_column(df) is None

    def test_find_date_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame()
        assert DataFrameProcessor.find_date_column(df) is None

    def test_find_date_case_sensitive(self):
        """Test that Date search is case-sensitive."""
        df = pd.DataFrame({"date": ["2024-01"], "Value": [100]})
        assert DataFrameProcessor.find_date_column(df) is None

    def test_find_date_mixed_columns(self):
        """Test finding Date among mixed single and MultiIndex columns."""
        # In practice this doesn't happen, but test robustness
        df = pd.DataFrame({"Date": ["2024-01"], "Other": [100]})
        assert DataFrameProcessor.find_date_column(df) == "Date"


class TestSumMonetaryColumns:
    """Tests for summing monetary columns in a row."""

    def test_sum_basic_row(self):
        """Test summing simple numeric row."""
        row = pd.Series({"Date": "2024-01", "Cash": "1000", "Stocks": "5000"})
        total = DataFrameProcessor.sum_monetary_columns_for_row(row, ["Date"])
        assert total == pytest.approx(6000.0)

    def test_sum_with_currency_symbols(self):
        """Test summing row with currency symbols."""
        row = pd.Series({"Date": "2024-01", "Cash": "€ 1.000", "Stocks": "€ 5.000"})
        total = DataFrameProcessor.sum_monetary_columns_for_row(row, ["Date"])
        assert total == pytest.approx(6000.0)

    def test_sum_exclude_multiple_patterns(self):
        """Test excluding multiple column patterns."""
        row = pd.Series(
            {
                "Date": "2024-01",
                "date_dt": "2024-01-01",
                "Category": "Savings",
                "Cash": "1000",
                "Stocks": "5000",
            }
        )
        total = DataFrameProcessor.sum_monetary_columns_for_row(
            row, ["Date", "date_dt", "Category"]
        )
        assert total == pytest.approx(6000.0)

    def test_sum_multiindex_columns(self):
        """Test summing MultiIndex columns."""
        row = pd.Series(
            {
                ("Date", ""): "2024-01",
                ("Cash", "Checking"): "1000",
                ("Cash", "Savings"): "2000",
                ("Investments", "Stocks"): "5000",
            }
        )
        total = DataFrameProcessor.sum_monetary_columns_for_row(row, ["Date", "date_dt"])
        assert total == pytest.approx(8000.0)

    def test_sum_with_nan_values(self):
        """Test summing row with NaN values (should be skipped)."""
        row = pd.Series({"Date": "2024-01", "Cash": "1000", "Stocks": None, "Bonds": ""})
        total = DataFrameProcessor.sum_monetary_columns_for_row(row, ["Date"])
        assert total == pytest.approx(1000.0)

    def test_sum_exclude_pattern_in_multiindex(self):
        """Test excluding patterns in MultiIndex column names."""
        row = pd.Series(
            {
                ("Date", "Value"): "2024-01",
                ("date_dt", ""): "2024-01-01",
                ("Cash", "Total"): "1000",
            }
        )
        total = DataFrameProcessor.sum_monetary_columns_for_row(row, ["Date", "date_dt"])
        assert total == pytest.approx(1000.0)

    def test_sum_empty_row(self):
        """Test summing empty row."""
        row = pd.Series({})
        total = DataFrameProcessor.sum_monetary_columns_for_row(row, [])
        assert total == pytest.approx(0.0)

    def test_sum_all_excluded(self):
        """Test when all columns are excluded."""
        row = pd.Series({"Date": "2024-01", "Category": "Foo"})
        total = DataFrameProcessor.sum_monetary_columns_for_row(row, ["Date", "Category"])
        assert total == pytest.approx(0.0)


class TestPreprocessExpenses:
    """Tests for preprocessing expenses DataFrame."""

    def test_preprocess_expenses_basic(self):
        """Test basic expenses preprocessing with string dates."""
        df = pd.DataFrame(
            {
                "Date": ["2024-01", "2024-02"],
                "Merchant": ["Store A", "Store B"],
                "Amount": ["€ 100", "€ 200"],
                "Category": ["Food", "Transport"],
                "Type": ["Variable", "Fixed"],
            }
        )
        result = DataFrameProcessor.preprocess_expenses(df)

        assert result is not None
        assert COL_DATE_DT in result.columns
        assert COL_AMOUNT_PARSED in result.columns
        assert len(result) == 2
        assert result[COL_AMOUNT_PARSED].tolist() == [100.0, 200.0]

    def test_preprocess_expenses_datetime_dates(self):
        """Test expenses preprocessing with datetime objects."""
        df = pd.DataFrame(
            {
                "Date": pd.to_datetime(["2024-01-15", "2024-02-20"]),
                "Merchant": ["Store A", "Store B"],
                "Amount": ["€ 100", "€ 200"],
                "Category": ["Food", "Transport"],
                "Type": ["Variable", "Fixed"],
            }
        )
        result = DataFrameProcessor.preprocess_expenses(df)

        assert result is not None
        assert COL_DATE_DT in result.columns
        # Dates should be normalized to first day of month
        assert result[COL_DATE_DT].dt.day.tolist() == [1, 1]

    def test_preprocess_expenses_missing_date_column(self):
        """Test expenses preprocessing with missing Date column."""
        df = pd.DataFrame(
            {
                "Month": ["2024-01"],
                "Amount": ["€ 100"],
            }
        )
        result = DataFrameProcessor.preprocess_expenses(df)
        assert result is None

    def test_preprocess_expenses_missing_amount_column(self):
        """Test expenses preprocessing with missing Amount column."""
        df = pd.DataFrame(
            {
                "Date": ["2024-01"],
                "Merchant": ["Store A"],
            }
        )
        result = DataFrameProcessor.preprocess_expenses(df)
        assert result is None

    def test_preprocess_expenses_none_input(self):
        """Test expenses preprocessing with None input."""
        result = DataFrameProcessor.preprocess_expenses(None)
        assert result is None

    def test_preprocess_expenses_invalid_dates(self):
        """Test expenses preprocessing with some invalid dates."""
        df = pd.DataFrame(
            {
                "Date": ["2024-01", "invalid", "2024-03"],
                "Merchant": ["A", "B", "C"],
                "Amount": ["100", "200", "300"],
                "Category": ["X", "Y", "Z"],
                "Type": ["T1", "T2", "T3"],
            }
        )
        result = DataFrameProcessor.preprocess_expenses(df)

        assert result is not None
        # Invalid date should be NaT
        assert result[COL_DATE_DT].isna().sum() == 1

    def test_preprocess_expenses_sorting(self):
        """Test that expenses are sorted by date."""
        df = pd.DataFrame(
            {
                "Date": ["2024-03", "2024-01", "2024-02"],
                "Merchant": ["C", "A", "B"],
                "Amount": ["300", "100", "200"],
                "Category": ["Z", "X", "Y"],
                "Type": ["T3", "T1", "T2"],
            }
        )
        result = DataFrameProcessor.preprocess_expenses(df)

        assert result is not None
        # Should be sorted by date
        merchants = result["Merchant"].tolist()
        assert merchants == ["A", "B", "C"]


class TestPreprocessAssets:
    """Tests for preprocessing assets DataFrame."""

    def test_preprocess_assets_single_index(self):
        """Test assets preprocessing with single-level columns."""
        df = pd.DataFrame(
            {
                "Date": ["2024-01", "2024-02"],
                "Cash": ["1000", "1100"],
                "Stocks": ["5000", "5500"],
            }
        )
        result = DataFrameProcessor.preprocess_assets(df)

        assert result is not None
        assert COL_DATE_DT in result.columns
        assert len(result) == 2

    def test_preprocess_assets_multiindex(self):
        """Test assets preprocessing with MultiIndex columns."""
        df = pd.DataFrame(
            {
                ("Date", ""): ["2024-01", "2024-02"],
                ("Cash", "Checking"): ["1000", "1100"],
                ("Cash", "Savings"): ["2000", "2200"],
                ("Investments", "Stocks"): ["5000", "5500"],
            }
        )
        result = DataFrameProcessor.preprocess_assets(df)

        assert result is not None
        assert COL_DATE_DT in result.columns
        assert len(result) == 2

    def test_preprocess_assets_none_input(self):
        """Test assets preprocessing with None input."""
        result = DataFrameProcessor.preprocess_assets(None)
        assert result is None

    def test_preprocess_assets_empty_dataframe(self):
        """Test assets preprocessing with empty DataFrame."""
        df = pd.DataFrame()
        result = DataFrameProcessor.preprocess_assets(df)
        assert result is None

    def test_preprocess_assets_no_date_column(self):
        """Test assets preprocessing without Date column."""
        df = pd.DataFrame(
            {
                "Cash": ["1000"],
                "Stocks": ["5000"],
            }
        )
        result = DataFrameProcessor.preprocess_assets(df)

        # Should still return DataFrame but without date_dt column
        assert result is not None
        assert COL_DATE_DT not in result.columns

    def test_preprocess_assets_sorting(self):
        """Test that assets are sorted by date."""
        df = pd.DataFrame(
            {
                "Date": ["2024-03", "2024-01", "2024-02"],
                "Cash": ["1200", "1000", "1100"],
            }
        )
        result = DataFrameProcessor.preprocess_assets(df)

        assert result is not None
        cash_values = result["Cash"].tolist()
        assert cash_values == ["1000", "1100", "1200"]


class TestPreprocessLiabilities:
    """Tests for preprocessing liabilities DataFrame."""

    def test_preprocess_liabilities_single_index(self):
        """Test liabilities preprocessing with single-level columns."""
        df = pd.DataFrame(
            {
                "Date": ["2024-01", "2024-02"],
                "Mortgage": ["100000", "99000"],
                "Loan": ["5000", "4500"],
            }
        )
        result = DataFrameProcessor.preprocess_liabilities(df)

        assert result is not None
        assert COL_DATE_DT in result.columns
        assert len(result) == 2

    def test_preprocess_liabilities_multiindex(self):
        """Test liabilities preprocessing with MultiIndex columns."""
        df = pd.DataFrame(
            {
                ("Date", ""): ["2024-01", "2024-02"],
                ("Mortgage", ""): ["100000", "99000"],
                ("Loans", "Car"): ["5000", "4500"],
            }
        )
        result = DataFrameProcessor.preprocess_liabilities(df)

        assert result is not None
        assert COL_DATE_DT in result.columns

    def test_preprocess_liabilities_none_input(self):
        """Test liabilities preprocessing with None input."""
        result = DataFrameProcessor.preprocess_liabilities(None)
        assert result is None

    def test_preprocess_liabilities_empty_dataframe(self):
        """Test liabilities preprocessing with empty DataFrame."""
        df = pd.DataFrame()
        result = DataFrameProcessor.preprocess_liabilities(df)
        assert result is None


class TestPreprocessIncomes:
    """Tests for preprocessing incomes DataFrame."""

    def test_preprocess_incomes_single_index(self):
        """Test incomes preprocessing with single-level columns."""
        df = pd.DataFrame(
            {
                "Date": ["2024-01", "2024-02"],
                "Salary": ["3000", "3000"],
                "Freelance": ["500", "750"],
            }
        )
        result = DataFrameProcessor.preprocess_incomes(df)

        assert result is not None
        assert COL_DATE_DT in result.columns
        assert len(result) == 2

    def test_preprocess_incomes_multiindex(self):
        """Test incomes preprocessing with MultiIndex columns."""
        df = pd.DataFrame(
            {
                ("Date", ""): ["2024-01", "2024-02"],
                ("Salary", ""): ["3000", "3000"],
                ("Freelance", "Project A"): ["500", "0"],
                ("Freelance", "Project B"): ["0", "750"],
            }
        )
        result = DataFrameProcessor.preprocess_incomes(df)

        assert result is not None
        assert COL_DATE_DT in result.columns

    def test_preprocess_incomes_none_input(self):
        """Test incomes preprocessing with None input."""
        result = DataFrameProcessor.preprocess_incomes(None)
        assert result is None

    def test_preprocess_incomes_empty_dataframe(self):
        """Test incomes preprocessing with empty DataFrame."""
        df = pd.DataFrame()
        result = DataFrameProcessor.preprocess_incomes(df)
        assert result is None

    def test_preprocess_incomes_sorting(self):
        """Test that incomes are sorted by date."""
        df = pd.DataFrame(
            {
                "Date": ["2024-03", "2024-01", "2024-02"],
                "Salary": ["3000", "3000", "3000"],
            }
        )
        result = DataFrameProcessor.preprocess_incomes(df)

        assert result is not None
        # Check sorted by extracting date_dt column
        dates = result[COL_DATE_DT].dt.strftime("%Y-%m").tolist()
        assert dates == ["2024-01", "2024-02", "2024-03"]
