"""Unit tests for table formatting logic (AG Grid column/row preparation)."""

import pandas as pd
import pytest

from app.logic.table_formatters import (
    build_aggrid_columns_from_dataframe,
    parse_dataframe_monetary_values,
    prepare_dataframe_for_aggrid,
)


class TestBuildAggridColumnsFromDataframe:
    """Test AG Grid column definitions builder."""

    def test_single_level_columns(self):
        """Test with simple single-level column names."""
        df = pd.DataFrame(
            {
                "Date": ["2024-01"],
                "Cash": [10000.50],
                "Stocks": [50000.75],
            }
        )
        formatter = "value + ' €'"

        columns = build_aggrid_columns_from_dataframe(df, formatter)

        # Should have Date + 2 value columns
        assert len(columns) == 3

        # Date column
        assert columns[0]["field"] == "Date"
        assert columns[0]["pinned"] == "left"
        assert columns[0]["sort"] == "desc"

        # Cash column
        assert columns[1]["field"] == "Cash"
        assert columns[1]["valueFormatter"] == formatter
        assert columns[1]["cellStyle"] == {"fontFamily": "monospace"}
        assert columns[1]["type"] == "rightAligned"

        # Stocks column
        assert columns[2]["field"] == "Stocks"
        assert columns[2]["valueFormatter"] == formatter

    def test_multi_level_columns(self):
        """Test with multi-level (tuple) column names."""
        df = pd.DataFrame(
            {
                ("Date", ""): ["2024-01"],
                ("Cash", "Checking"): [5000.0],
                ("Cash", "Savings"): [10000.0],
                ("Investments", "Stocks"): [50000.0],
            }
        )
        formatter = "value + ' $'"

        columns = build_aggrid_columns_from_dataframe(df, formatter)

        # Date + 2 groups (Cash, Investments)
        assert len(columns) == 3

        # Date column
        assert columns[0]["field"] == "Date"

        # Cash group with 2 children
        assert columns[1]["headerName"] == "Cash"
        assert "children" in columns[1]
        assert len(columns[1]["children"]) == 2
        assert columns[1]["children"][0]["field"] == "Cash_Checking"
        assert columns[1]["children"][0]["headerName"] == "Checking"
        assert columns[1]["children"][0]["valueFormatter"] == formatter
        assert columns[1]["children"][0]["cellStyle"] == {"fontFamily": "monospace"}
        assert columns[1]["children"][1]["field"] == "Cash_Savings"

        # Investments group with 1 child
        assert columns[2]["headerName"] == "Investments"
        assert len(columns[2]["children"]) == 1
        assert columns[2]["children"][0]["field"] == "Investments_Stocks"

    def test_mixed_single_and_multi_level(self):
        """Test with both single and multi-level columns."""
        df = pd.DataFrame(
            {
                "Date": ["2024-01"],
                "Total": [100000.0],  # Single level
                ("Cash", "Checking"): [5000.0],  # Multi level
                ("Cash", "Savings"): [10000.0],
            }
        )
        formatter = "value"

        columns = build_aggrid_columns_from_dataframe(df, formatter)

        # Date + Total + Cash group
        assert len(columns) == 3
        assert columns[0]["field"] == "Date"
        assert columns[1]["field"] == "Total"  # Single level
        assert columns[2]["headerName"] == "Cash"  # Multi level group

    def test_skips_date_columns(self):
        """Test that date_dt column is skipped."""
        df = pd.DataFrame(
            {
                "Date": ["2024-01"],
                "date_dt": [pd.Timestamp("2024-01-01")],
                "Cash": [5000.0],
            }
        )
        formatter = "value"

        columns = build_aggrid_columns_from_dataframe(df, formatter)

        # Should only have Date + Cash (date_dt skipped)
        assert len(columns) == 2
        assert columns[0]["field"] == "Date"
        assert columns[1]["field"] == "Cash"

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame({"Date": []})
        formatter = "value"

        columns = build_aggrid_columns_from_dataframe(df, formatter)

        # Should only have Date column
        assert len(columns) == 1
        assert columns[0]["field"] == "Date"

    def test_column_properties(self):
        """Test that columns have required AG Grid properties."""
        df = pd.DataFrame({"Date": ["2024-01"], "Value": [100.0]})
        formatter = "value + ' €'"

        columns = build_aggrid_columns_from_dataframe(df, formatter)

        value_col = columns[1]
        assert value_col["sortable"] is True
        assert value_col["type"] == "rightAligned"
        assert "minWidth" in value_col
        assert "flex" in value_col


class TestPrepareDataframeForAggrid:
    """Test DataFrame to AG Grid row data converter."""

    def test_single_level_dataframe(self):
        """Test with simple single-level DataFrame."""
        df = pd.DataFrame(
            {
                "date_dt": pd.to_datetime(["2024-01-15", "2024-02-20"]),
                "Cash": ["€ 5.000,50", "€ 6.000,75"],
                "Stocks": ["€ 50.000,00", "€ 52.000,00"],
            }
        )

        rows = prepare_dataframe_for_aggrid(df)

        assert len(rows) == 2

        # First row
        assert rows[0]["Date"] == "2024-01"
        assert rows[0]["Cash"] == pytest.approx(5000.50)
        assert rows[0]["Stocks"] == pytest.approx(50000.00)
        # Second row
        assert rows[1]["Date"] == "2024-02"
        assert rows[1]["Cash"] == pytest.approx(6000.75)

    def test_multi_level_dataframe(self):
        """Test with multi-level (tuple) columns."""
        df = pd.DataFrame(
            {
                ("Date", ""): ["2024-01"],
                ("Cash", "Checking"): ["€ 5.000,00"],
                ("Cash", "Savings"): ["€ 10.000,00"],
            }
        )
        # Need to set proper datetime column for date handling
        df[("date_dt", "")] = pd.to_datetime(["2024-01-15"])

        rows = prepare_dataframe_for_aggrid(df)

        assert len(rows) == 1
        assert rows[0]["Date"] == "2024-01"
        assert rows[0]["Cash_Checking"] == pytest.approx(5000.00)
        assert rows[0]["Cash_Savings"] == pytest.approx(10000.00)

    def test_date_formatting(self):
        """Test various date format handling."""
        df = pd.DataFrame(
            {
                "date_dt": pd.to_datetime(["2024-01-01", "2024-12-31"]),
                "Value": [100, 200],
            }
        )

        rows = prepare_dataframe_for_aggrid(df)

        # Should format to YYYY-MM
        assert rows[0]["Date"] == "2024-01"
        assert rows[1]["Date"] == "2024-12"

    def test_monetary_value_parsing(self):
        """Test parsing of various monetary formats."""
        df = pd.DataFrame(
            {
                "date_dt": pd.to_datetime(["2024-01-01"]),
                "EUR": ["€ 1.234,56"],  # European
                "USD": ["$ 1,234.56"],  # US
                "Plain": ["1234.56"],  # Plain number
                "Spaces": [" € 5.000,00 "],  # With spaces
                "JPY": ["¥ 1,234"],  # No decimals
            }
        )

        rows = prepare_dataframe_for_aggrid(df)

        assert rows[0]["EUR"] == pytest.approx(1234.56)
        assert rows[0]["USD"] == pytest.approx(1234.56)
        assert rows[0]["Plain"] == pytest.approx(1234.56)
        assert rows[0]["Spaces"] == pytest.approx(5000.00)
        assert rows[0]["JPY"] == pytest.approx(1234.00)

    def test_none_and_empty_handling(self):
        """Test handling of None and empty string values."""
        df = pd.DataFrame(
            {
                "date_dt": pd.to_datetime(["2024-01-01"]),
                "WithNone": [None],
                "WithEmpty": [""],
                "WithDash": ["-"],
            }
        )

        rows = prepare_dataframe_for_aggrid(df)

        # Should convert to 0.0
        assert rows[0]["WithNone"] == pytest.approx(0.0)
        assert rows[0]["WithEmpty"] == pytest.approx(0.0)
        assert rows[0]["WithDash"] == pytest.approx(0.0)

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame({"date_dt": [], "Value": []})
        df["date_dt"] = pd.to_datetime(df["date_dt"])

        rows = prepare_dataframe_for_aggrid(df)

        assert len(rows) == 0


class TestParseDataframeMonetaryValues:
    """Test DataFrame monetary value parsing while preserving column structure."""

    def test_single_level_columns(self):
        """Test parsing with single-level columns."""
        df = pd.DataFrame(
            {
                "date_dt": pd.to_datetime(["2024-01-01"]),
                "Cash": ["1.234,56 €"],  # European format
                "Stocks": ["5000,00 €"],  # No thousands separator for clearer parsing
            }
        )

        result = parse_dataframe_monetary_values(df)

        # Check values are parsed
        assert result["Cash"].iloc[0] == pytest.approx(1234.56)
        assert result["Stocks"].iloc[0] == pytest.approx(5000.00)
        # Check Date_DT is preserved
        assert result["date_dt"].iloc[0] == pd.Timestamp("2024-01-01")

    def test_multi_level_columns_preserved(self):
        """Test that multi-level columns are preserved."""
        df = pd.DataFrame(
            {
                "date_dt": pd.to_datetime(["2024-01-01"]),
                ("Cash", "Checking"): ["1000,00 €"],
                ("Cash", "Savings"): ["5000,00 €"],
                ("Investments", "Stocks"): ["10000,00 €"],
            }
        )

        result = parse_dataframe_monetary_values(df)

        # Check column structure is preserved
        assert ("Cash", "Checking") in result.columns
        assert ("Cash", "Savings") in result.columns
        assert ("Investments", "Stocks") in result.columns

        # Check values are parsed
        assert result[("Cash", "Checking")].iloc[0] == pytest.approx(1000.00)
        assert result[("Cash", "Savings")].iloc[0] == pytest.approx(5000.00)
        assert result[("Investments", "Stocks")].iloc[0] == pytest.approx(10000.00)

    def test_nan_handling(self):
        """Test that NaN values are converted to 0.0."""
        df = pd.DataFrame(
            {
                "date_dt": pd.to_datetime(["2024-01-01"]),
                "WithNaN": [None],
                "WithValue": ["€ 100,00"],
            }
        )

        result = parse_dataframe_monetary_values(df)

        assert result["WithNaN"].iloc[0] == pytest.approx(0.0)
        assert result["WithValue"].iloc[0] == pytest.approx(100.00)

    def test_skips_date_dt_column(self):
        """Test that date_dt column is not parsed as monetary."""
        df = pd.DataFrame(
            {
                "date_dt": pd.to_datetime(["2024-01-01", "2024-02-01"]),
                "Value": ["€ 100,00", "€ 200,00"],
            }
        )

        result = parse_dataframe_monetary_values(df)

        # date_dt should remain datetime, not parsed
        assert pd.api.types.is_datetime64_any_dtype(result["date_dt"])
        assert result["date_dt"].iloc[0] == pd.Timestamp("2024-01-01")
        assert result["Value"].iloc[0] == pytest.approx(100.00)

    def test_skips_date_column(self):
        """Test that Date column (string dates) is not parsed as monetary."""
        df = pd.DataFrame(
            {
                "date_dt": pd.to_datetime(["2024-01-01", "2024-02-01"]),
                "Date": ["2024-01", "2024-02"],  # String dates like in actual data
                "Value": ["100,00 €", "200,00 €"],
            }
        )

        result = parse_dataframe_monetary_values(df)

        # Date column should remain as-is (strings), not converted to 0.0
        assert result["Date"].iloc[0] == "2024-01"
        assert result["Date"].iloc[1] == "2024-02"
        # Value column should be parsed
        assert result["Value"].iloc[0] == pytest.approx(100.00)
        assert result["Value"].iloc[1] == pytest.approx(200.00)

    def test_field_name_flattening(self):
        """Test that multi-level columns are flattened to Category_Item format."""
        df = pd.DataFrame(
            {
                ("date_dt", ""): pd.to_datetime(["2024-01-01"]),
                ("Real Estate", "Apartment"): ["€ 200.000,00"],
                ("Real Estate", "Land"): ["€ 50.000,00"],
            }
        )

        rows = prepare_dataframe_for_aggrid(df)

        # Spaces should be replaced with underscores
        assert "Real_Estate_Apartment" in rows[0]
        assert "Real_Estate_Land" in rows[0]
        assert rows[0]["Real_Estate_Apartment"] == pytest.approx(200000.00)

    def test_preserves_all_rows(self):
        """Test that all DataFrame rows are converted."""
        df = pd.DataFrame(
            {
                "date_dt": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01"]),
                "Value": [100, 200, 300, 400],
            }
        )

        rows = prepare_dataframe_for_aggrid(df)

        assert len(rows) == 4
        assert rows[0]["Value"] == pytest.approx(100.0)
        assert rows[1]["Value"] == pytest.approx(200.0)
        assert rows[2]["Value"] == pytest.approx(300.0)
        assert rows[3]["Value"] == pytest.approx(400.0)
