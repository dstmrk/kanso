"""
Tests for data_quality module.

Tests the DataQualityChecker class for detecting missing sheets, empty sheets,
and missing required columns.
"""

import pandas as pd
import pytest

from app.logic.data_quality import DataQualityChecker, DataQualityWarning


class TestDataQualityChecker:
    """Tests for DataQualityChecker class."""

    @pytest.fixture
    def checker(self):
        """Create a DataQualityChecker instance."""
        return DataQualityChecker()

    @pytest.fixture
    def valid_storage(self):
        """Create a valid storage dict with all sheets present and populated."""
        # Assets with MultiIndex columns
        assets_df = pd.DataFrame(
            {
                ("Date", ""): ["2024-01", "2024-02"],
                ("Cash", "Checking"): [1000, 1200],
                ("Investments", "Stocks"): [5000, 5500],
            }
        )

        # Liabilities with MultiIndex columns
        liabilities_df = pd.DataFrame(
            {
                ("Date", ""): ["2024-01", "2024-02"],
                ("Mortgage", ""): [250000, 248000],
                ("Loans", "Car"): [15000, 14000],
            }
        )

        # Incomes with MultiIndex columns
        incomes_df = pd.DataFrame(
            {
                ("Date", ""): ["2024-01", "2024-02"],
                ("Salary", ""): [3000, 3000],
                ("Freelance", "Project A"): [500, 600],
            }
        )

        # Expenses with single-level columns
        expenses_df = pd.DataFrame(
            {
                "Date": ["2024-01", "2024-02"],
                "Merchant": ["Store A", "Store B"],
                "Amount": ["€ 100", "€ 200"],
                "Category": ["Food", "Transport"],
                "Type": ["Variable", "Variable"],
            }
        )

        return {
            "assets_sheet": assets_df.to_json(orient="split"),
            "liabilities_sheet": liabilities_df.to_json(orient="split"),
            "incomes_sheet": incomes_df.to_json(orient="split"),
            "expenses_sheet": expenses_df.to_json(orient="split"),
        }

    def test_check_missing_sheets_all_present(self, checker, valid_storage):
        """Test that no warnings are generated when all sheets are present."""
        warnings = checker.check_missing_sheets(valid_storage)
        assert len(warnings) == 0

    def test_check_missing_sheets_one_missing(self, checker, valid_storage):
        """Test warning for one missing sheet."""
        del valid_storage["assets_sheet"]

        warnings = checker.check_missing_sheets(valid_storage)

        assert len(warnings) == 1
        assert warnings[0].sheet_name == "Assets"
        assert warnings[0].severity == "error"
        assert "not loaded" in warnings[0].message

    def test_check_missing_sheets_all_missing(self, checker):
        """Test warnings when all sheets are missing."""
        empty_storage = {}

        warnings = checker.check_missing_sheets(empty_storage)

        assert len(warnings) == 4
        sheet_names = {w.sheet_name for w in warnings}
        assert sheet_names == {"Assets", "Liabilities", "Incomes", "Expenses"}
        assert all(w.severity == "error" for w in warnings)

    def test_check_missing_sheets_none_value(self, checker, valid_storage):
        """Test that None values are treated as missing sheets."""
        valid_storage["assets_sheet"] = None

        warnings = checker.check_missing_sheets(valid_storage)

        assert len(warnings) == 1
        assert warnings[0].sheet_name == "Assets"

    def test_check_empty_sheets_all_have_data(self, checker, valid_storage):
        """Test that no warnings are generated when all sheets have data."""
        warnings = checker.check_empty_sheets(valid_storage)
        assert len(warnings) == 0

    def test_check_empty_sheets_one_empty(self, checker, valid_storage):
        """Test warning for one empty sheet."""
        # Create empty DataFrame
        empty_df = pd.DataFrame(columns=["Date", ("Cash", "Checking")])
        valid_storage["assets_sheet"] = empty_df.to_json(orient="split")

        warnings = checker.check_empty_sheets(valid_storage)

        assert len(warnings) == 1
        assert warnings[0].sheet_name == "Assets"
        assert warnings[0].severity == "warning"
        assert "no data" in warnings[0].message

    def test_check_empty_sheets_multiindex_empty(self, checker, valid_storage):
        """Test warning for empty MultiIndex sheet."""
        # Create empty MultiIndex DataFrame
        empty_df = pd.DataFrame(
            columns=pd.MultiIndex.from_tuples([("Date", ""), ("Cash", "Checking")])
        )
        valid_storage["liabilities_sheet"] = empty_df.to_json(orient="split")

        warnings = checker.check_empty_sheets(valid_storage)

        assert len(warnings) == 1
        assert warnings[0].sheet_name == "Liabilities"

    def test_check_empty_sheets_skip_missing(self, checker, valid_storage):
        """Test that missing sheets are skipped (not reported as empty)."""
        del valid_storage["assets_sheet"]

        warnings = checker.check_empty_sheets(valid_storage)

        # Should not report Assets as empty, since it's missing
        sheet_names = {w.sheet_name for w in warnings}
        assert "Assets" not in sheet_names

    def test_check_missing_columns_all_present(self, checker, valid_storage):
        """Test that no warnings when all required columns are present."""
        warnings = checker.check_missing_columns(valid_storage)
        assert len(warnings) == 0

    def test_check_missing_columns_date_missing_expenses(self, checker, valid_storage):
        """Test warning when Date column is missing from Expenses."""
        # Create Expenses without Date column
        expenses_df = pd.DataFrame(
            {
                "Merchant": ["Store A"],
                "Amount": ["€ 100"],
                "Category": ["Food"],
                "Type": ["Variable"],
            }
        )
        valid_storage["expenses_sheet"] = expenses_df.to_json(orient="split")

        warnings = checker.check_missing_columns(valid_storage)

        assert len(warnings) == 1
        assert warnings[0].sheet_name == "Expenses"
        assert warnings[0].severity == "error"
        assert "Date" in warnings[0].details

    def test_check_missing_columns_multiple_missing_expenses(self, checker, valid_storage):
        """Test warning when multiple columns are missing from Expenses."""
        # Create Expenses with only Date column
        expenses_df = pd.DataFrame({"Date": ["2024-01"]})
        valid_storage["expenses_sheet"] = expenses_df.to_json(orient="split")

        warnings = checker.check_missing_columns(valid_storage)

        assert len(warnings) == 1
        assert warnings[0].sheet_name == "Expenses"
        assert "Merchant" in warnings[0].details
        assert "Amount" in warnings[0].details
        assert "Category" in warnings[0].details
        assert "Type" in warnings[0].details

    def test_check_missing_columns_date_missing_multiindex(self, checker, valid_storage):
        """Test warning when Date column is missing from MultiIndex sheet."""
        # Create Assets without Date column
        assets_df = pd.DataFrame(
            {
                ("Cash", "Checking"): [1000],
                ("Investments", "Stocks"): [5000],
            }
        )
        valid_storage["assets_sheet"] = assets_df.to_json(orient="split")

        warnings = checker.check_missing_columns(valid_storage)

        assert len(warnings) == 1
        assert warnings[0].sheet_name == "Assets"
        assert "Date" in warnings[0].details

    def test_check_missing_columns_skip_empty_sheets(self, checker, valid_storage):
        """Test that empty sheets are skipped (not checked for columns)."""
        # Make Assets empty
        empty_df = pd.DataFrame()
        valid_storage["assets_sheet"] = empty_df.to_json(orient="split")

        warnings = checker.check_missing_columns(valid_storage)

        # Should not report missing columns for empty sheet
        sheet_names = {w.sheet_name for w in warnings}
        assert "Assets" not in sheet_names

    def test_check_all_no_issues(self, checker, valid_storage):
        """Test check_all with no data quality issues."""
        warnings = checker.check_all(valid_storage)
        assert len(warnings) == 0

    def test_check_all_multiple_issues(self, checker, valid_storage):
        """Test check_all with multiple data quality issues."""
        # Create multiple issues:
        # 1. Missing sheet (Assets)
        del valid_storage["assets_sheet"]

        # 2. Empty sheet (Liabilities)
        empty_df = pd.DataFrame()
        valid_storage["liabilities_sheet"] = empty_df.to_json(orient="split")

        # 3. Missing column (Expenses without Date)
        expenses_df = pd.DataFrame(
            {
                "Merchant": ["Store A"],
                "Amount": ["€ 100"],
                "Category": ["Food"],
                "Type": ["Variable"],
            }
        )
        valid_storage["expenses_sheet"] = expenses_df.to_json(orient="split")

        warnings = checker.check_all(valid_storage)

        # Should have 3 warnings total
        assert len(warnings) == 3

        # Verify each type of warning is present
        sheet_names = {w.sheet_name for w in warnings}
        assert "Assets" in sheet_names  # Missing
        assert "Liabilities" in sheet_names  # Empty
        assert "Expenses" in sheet_names  # Missing column

    def test_check_all_only_errors(self, checker):
        """Test check_all with only error-level issues."""
        empty_storage = {}

        warnings = checker.check_all(empty_storage)

        # All sheets missing = 4 errors
        assert len(warnings) == 4
        assert all(w.severity == "error" for w in warnings)

    def test_data_quality_warning_structure(self):
        """Test DataQualityWarning dataclass structure."""
        warning = DataQualityWarning(
            sheet_name="Assets",
            severity="error",
            message="Test message",
            details="Test details",
        )

        assert warning.sheet_name == "Assets"
        assert warning.severity == "error"
        assert warning.message == "Test message"
        assert warning.details == "Test details"

    def test_data_quality_warning_optional_details(self):
        """Test DataQualityWarning with optional details."""
        warning = DataQualityWarning(
            sheet_name="Expenses",
            severity="warning",
            message="Test message",
        )

        assert warning.details is None

    def test_required_sheets_constant(self, checker):
        """Test that REQUIRED_SHEETS contains all expected sheets."""
        assert len(checker.REQUIRED_SHEETS) == 4
        assert "assets_sheet" in checker.REQUIRED_SHEETS
        assert "liabilities_sheet" in checker.REQUIRED_SHEETS
        assert "incomes_sheet" in checker.REQUIRED_SHEETS
        assert "expenses_sheet" in checker.REQUIRED_SHEETS

    def test_required_columns_constant(self, checker):
        """Test that REQUIRED_COLUMNS defines columns for all sheets."""
        assert len(checker.REQUIRED_COLUMNS) == 4

        # All sheets require Date column
        for sheet in checker.REQUIRED_SHEETS:
            assert "Date" in checker.REQUIRED_COLUMNS[sheet]

        # Expenses has additional required columns
        assert "Merchant" in checker.REQUIRED_COLUMNS["expenses_sheet"]
        assert "Amount" in checker.REQUIRED_COLUMNS["expenses_sheet"]
        assert "Category" in checker.REQUIRED_COLUMNS["expenses_sheet"]
        assert "Type" in checker.REQUIRED_COLUMNS["expenses_sheet"]
