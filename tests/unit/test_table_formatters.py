"""Unit tests for table formatting logic (AG Grid column/row preparation)."""

import pandas as pd

from app.logic.table_formatters import (
    build_aggrid_columns_from_dataframe,
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
        assert rows[0]["Cash"] == 5000.50
        assert rows[0]["Stocks"] == 50000.00

        # Second row
        assert rows[1]["Date"] == "2024-02"
        assert rows[1]["Cash"] == 6000.75

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
        assert rows[0]["Cash_Checking"] == 5000.00
        assert rows[0]["Cash_Savings"] == 10000.00

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

        assert rows[0]["EUR"] == 1234.56
        assert rows[0]["USD"] == 1234.56
        assert rows[0]["Plain"] == 1234.56
        assert rows[0]["Spaces"] == 5000.00
        assert rows[0]["JPY"] == 1234.00

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
        assert rows[0]["WithNone"] == 0.0
        assert rows[0]["WithEmpty"] == 0.0
        assert rows[0]["WithDash"] == 0.0

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame({"date_dt": [], "Value": []})
        df["date_dt"] = pd.to_datetime(df["date_dt"])

        rows = prepare_dataframe_for_aggrid(df)

        assert len(rows) == 0

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
        assert rows[0]["Real_Estate_Apartment"] == 200000.00

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
        assert rows[0]["Value"] == 100.0
        assert rows[1]["Value"] == 200.0
        assert rows[2]["Value"] == 300.0
        assert rows[3]["Value"] == 400.0
