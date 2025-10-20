"""
Tests for validators module.

Tests Pydantic validation models for data sheet and expenses sheet.
"""

import pytest
from pydantic import ValidationError

from app.core.validators import DataSheetRow, ExpenseRow, validate_dataframe_structure


class TestDataSheetRow:
    """Tests for DataSheetRow validation model."""

    def test_valid_date_format(self):
        """Test valid YYYY-MM date format."""
        row = DataSheetRow(Date="2024-01", Net_Worth="€ 1.000")
        assert row.Date == "2024-01"

    def test_invalid_date_format_day(self):
        """Test invalid date with day included."""
        with pytest.raises(ValidationError) as exc_info:
            DataSheetRow(Date="2024-01-15")
        assert "Date must be in YYYY-MM format" in str(exc_info.value)

    def test_invalid_date_format_text(self):
        """Test invalid date with text."""
        with pytest.raises(ValidationError) as exc_info:
            DataSheetRow(Date="January 2024")
        assert "Date must be in YYYY-MM format" in str(exc_info.value)

    def test_empty_date(self):
        """Test empty date raises error."""
        with pytest.raises(ValidationError) as exc_info:
            DataSheetRow(Date="")
        assert "Date cannot be empty" in str(exc_info.value)

    def test_date_with_whitespace(self):
        """Test date with whitespace is stripped."""
        row = DataSheetRow(Date="  2024-01  ")
        assert row.Date == "2024-01"

    def test_valid_monetary_fields(self):
        """Test valid monetary field formats."""
        row = DataSheetRow(
            Date="2024-01", Net_Worth="€ 10.000", Income="$ 5,000.00", Expenses="3000"
        )
        assert row.Net_Worth == "€ 10.000"
        assert row.Income == "$ 5,000.00"
        assert row.Expenses == "3000"

    def test_empty_monetary_fields(self):
        """Test empty monetary fields are allowed."""
        row = DataSheetRow(Date="2024-01", Net_Worth="", Income=None)
        assert row.Net_Worth is None
        assert row.Income is None

    def test_monetary_field_without_digits(self):
        """Test monetary field without digits returns None."""
        row = DataSheetRow(Date="2024-01", Net_Worth="€€€")
        # Should log warning but not raise error, returns None
        assert row.Net_Worth is None

    def test_all_monetary_columns(self):
        """Test all monetary columns are accepted."""
        row = DataSheetRow(
            Date="2024-01",
            Cash="€ 1.000",
            Pension_Fund="€ 2.000",
            Stocks="€ 3.000",
            Real_Estate="€ 4.000",
            Crypto="€ 500",
            Other="€ 100",
            Mortgage="€ 10.000",
            Loans="€ 5.000",
        )
        assert row.Cash == "€ 1.000"
        assert row.Pension_Fund == "€ 2.000"
        assert row.Loans == "€ 5.000"

    def test_extra_fields_allowed(self):
        """Test extra fields are allowed with extra='allow' config."""
        row = DataSheetRow(Date="2024-01", Extra_Field="Some value", Another_Field="123")
        # Should not raise error due to extra='allow'
        assert row.Date == "2024-01"


class TestExpenseRow:
    """Tests for ExpenseRow validation model."""

    def test_valid_expense_row(self):
        """Test valid expense row."""
        row = ExpenseRow(
            Date="2024-01", Merchant="Amazon", Amount="€ 500", Category="Food", Type="Variable"
        )
        assert row.Date == "2024-01"
        assert row.Merchant == "Amazon"
        assert row.Category == "Food"
        assert row.Amount == "€ 500"
        assert row.Type == "Variable"

    def test_invalid_date_format(self):
        """Test invalid date format."""
        with pytest.raises(ValidationError) as exc_info:
            ExpenseRow(
                Date="01-2024",
                Merchant="Amazon",
                Category="Food",
                Amount="€ 500",
                Type="Variable",
            )
        assert "Date must be in YYYY-MM format" in str(exc_info.value)

    def test_empty_date(self):
        """Test empty date raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ExpenseRow(Date="", Merchant="Amazon", Category="Food", Amount="€ 500", Type="Variable")
        assert "Date cannot be empty" in str(exc_info.value)

    def test_date_with_whitespace(self):
        """Test date with whitespace is stripped."""
        row = ExpenseRow(
            Date="  2024-01  ",
            Merchant="Amazon",
            Category="Food",
            Amount="€ 500",
            Type="Variable",
        )
        assert row.Date == "2024-01"

    def test_valid_merchant(self):
        """Test valid merchant."""
        row = ExpenseRow(
            Date="2024-01",
            Merchant="Local Grocery",
            Category="Food",
            Amount="€ 500",
            Type="Variable",
        )
        assert row.Merchant == "Local Grocery"

    def test_empty_merchant(self):
        """Test empty merchant raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ExpenseRow(
                Date="2024-01", Merchant="", Category="Food", Amount="€ 500", Type="Variable"
            )
        assert "Merchant cannot be empty" in str(exc_info.value)

    def test_merchant_with_whitespace(self):
        """Test merchant with whitespace is stripped."""
        row = ExpenseRow(
            Date="2024-01",
            Merchant="  Amazon  ",
            Category="Food",
            Amount="€ 500",
            Type="Variable",
        )
        assert row.Merchant == "Amazon"

    def test_valid_category(self):
        """Test valid category."""
        row = ExpenseRow(
            Date="2024-01",
            Merchant="Netflix",
            Category="Entertainment",
            Amount="€ 200",
            Type="Fixed",
        )
        assert row.Category == "Entertainment"

    def test_empty_category(self):
        """Test empty category raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ExpenseRow(
                Date="2024-01", Merchant="Amazon", Category="", Amount="€ 500", Type="Variable"
            )
        assert "Category cannot be empty" in str(exc_info.value)

    def test_whitespace_only_category(self):
        """Test whitespace-only category raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ExpenseRow(
                Date="2024-01", Merchant="Amazon", Category="   ", Amount="€ 500", Type="Variable"
            )
        assert "Category cannot be empty" in str(exc_info.value)

    def test_category_with_whitespace(self):
        """Test category with whitespace is stripped."""
        row = ExpenseRow(
            Date="2024-01",
            Merchant="Amazon",
            Category="  Food  ",
            Amount="€ 500",
            Type="Variable",
        )
        assert row.Category == "Food"

    def test_valid_type(self):
        """Test valid type."""
        row = ExpenseRow(
            Date="2024-01",
            Merchant="Netflix",
            Category="Entertainment",
            Amount="€ 200",
            Type="Fixed",
        )
        assert row.Type == "Fixed"

    def test_empty_type(self):
        """Test empty type raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ExpenseRow(Date="2024-01", Merchant="Amazon", Category="Food", Amount="€ 500", Type="")
        assert "Type cannot be empty" in str(exc_info.value)

    def test_type_with_whitespace(self):
        """Test type with whitespace is stripped."""
        row = ExpenseRow(
            Date="2024-01",
            Merchant="Amazon",
            Category="Food",
            Amount="€ 500",
            Type="  Variable  ",
        )
        assert row.Type == "Variable"

    def test_valid_amount_formats(self):
        """Test various valid amount formats."""
        row1 = ExpenseRow(
            Date="2024-01",
            Merchant="Amazon",
            Category="Food",
            Amount="€ 1.234,56",
            Type="Variable",
        )
        row2 = ExpenseRow(
            Date="2024-01",
            Merchant="Amazon",
            Category="Food",
            Amount="$ 1,234.56",
            Type="Variable",
        )
        row3 = ExpenseRow(
            Date="2024-01", Merchant="Amazon", Category="Food", Amount="1000", Type="Variable"
        )

        assert row1.Amount == "€ 1.234,56"
        assert row2.Amount == "$ 1,234.56"
        assert row3.Amount == "1000"

    def test_empty_amount(self):
        """Test empty amount raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ExpenseRow(
                Date="2024-01", Merchant="Amazon", Category="Food", Amount="", Type="Variable"
            )
        assert "Amount cannot be empty" in str(exc_info.value)

    def test_amount_without_digits(self):
        """Test amount without digits raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ExpenseRow(
                Date="2024-01", Merchant="Amazon", Category="Food", Amount="€€€", Type="Variable"
            )
        assert "Amount must contain numbers" in str(exc_info.value)


class TestValidateDataframeStructure:
    """Tests for validate_dataframe_structure helper function."""

    def test_valid_data_sheet_data(self):
        """Test validation with valid data sheet rows."""
        data = [
            {"Date": "2024-01", "Net_Worth": "€ 10.000", "Income": "€ 3.000"},
            {"Date": "2024-02", "Net_Worth": "€ 11.000", "Income": "€ 3.000"},
            {"Date": "2024-03", "Net_Worth": "€ 12.000", "Income": "€ 3.000"},
        ]

        is_valid, errors = validate_dataframe_structure(data, DataSheetRow)

        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_data_sheet_data(self):
        """Test validation with invalid data sheet rows."""
        data = [
            {"Date": "invalid-date", "Net_Worth": "€ 10.000"},
            {"Date": "2024-02", "Net_Worth": "€ 11.000"},
            {"Date": "", "Net_Worth": "€ 12.000"},
        ]

        is_valid, errors = validate_dataframe_structure(data, DataSheetRow)

        assert is_valid is False
        assert len(errors) == 2  # Row 1 and Row 3 have invalid dates
        assert "Row 1:" in errors[0]
        assert "Row 3:" in errors[1]

    def test_valid_expense_data(self):
        """Test validation with valid expense rows."""
        data = [
            {
                "Date": "2024-01",
                "Merchant": "Grocery Store",
                "Amount": "€ 500",
                "Category": "Food",
                "Type": "Variable",
            },
            {
                "Date": "2024-01",
                "Merchant": "Gas Station",
                "Amount": "€ 300",
                "Category": "Transport",
                "Type": "Variable",
            },
            {
                "Date": "2024-01",
                "Merchant": "Landlord",
                "Amount": "€ 800",
                "Category": "Housing",
                "Type": "Fixed",
            },
        ]

        is_valid, errors = validate_dataframe_structure(data, ExpenseRow)

        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_expense_data(self):
        """Test validation with invalid expense rows."""
        data = [
            {
                "Date": "2024-01",
                "Merchant": "Store",
                "Amount": "€ 500",
                "Category": "Food",
                "Type": "Variable",
            },
            {"Date": "invalid", "Merchant": "", "Category": "", "Amount": "", "Type": ""},
            {
                "Date": "2024-02",
                "Merchant": "Store",
                "Amount": "€€€",
                "Category": "Transport",
                "Type": "Variable",
            },
        ]

        is_valid, errors = validate_dataframe_structure(data, ExpenseRow)

        assert is_valid is False
        assert len(errors) == 2  # Row 2 and Row 3 have errors
        assert "Row 2:" in errors[0]
        assert "Row 3:" in errors[1]

    def test_mixed_valid_and_invalid_rows(self):
        """Test validation with mix of valid and invalid rows."""
        data = [
            {"Date": "2024-01", "Net_Worth": "€ 10.000"},  # Valid
            {"Date": "bad-date", "Net_Worth": "€ 11.000"},  # Invalid date
            {"Date": "2024-03", "Net_Worth": "€ 12.000"},  # Valid
            {"Date": "", "Net_Worth": "€ 13.000"},  # Empty date
            {"Date": "2024-05", "Net_Worth": "€ 14.000"},  # Valid
        ]

        is_valid, errors = validate_dataframe_structure(data, DataSheetRow)

        assert is_valid is False
        assert len(errors) == 2
        assert "Row 2:" in errors[0]
        assert "Row 4:" in errors[1]

    def test_empty_data(self):
        """Test validation with empty data."""
        data = []

        is_valid, errors = validate_dataframe_structure(data, DataSheetRow)

        assert is_valid is True
        assert len(errors) == 0

    def test_many_errors(self):
        """Test validation with many errors (tests error limiting)."""
        # Create 20 rows with invalid dates
        data = [{"Date": f"invalid-{i}", "Net_Worth": f"€ {i}.000"} for i in range(20)]

        is_valid, errors = validate_dataframe_structure(data, DataSheetRow)

        assert is_valid is False
        assert len(errors) == 20  # All rows have errors
