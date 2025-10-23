"""
Tests for validators module.

Tests Pydantic validation models for expenses sheet.
"""

import pytest
from pydantic import ValidationError

from app.core.validators import ExpenseRow, validate_dataframe_structure


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
        """Test validation with mix of valid and invalid expense rows."""
        data = [
            {
                "Date": "2024-01",
                "Merchant": "Store",
                "Amount": "€ 100",
                "Category": "Food",
                "Type": "Variable",
            },  # Valid
            {
                "Date": "bad-date",
                "Merchant": "Store",
                "Amount": "€ 100",
                "Category": "Food",
                "Type": "Variable",
            },  # Invalid date
            {
                "Date": "2024-03",
                "Merchant": "Store",
                "Amount": "€ 100",
                "Category": "Food",
                "Type": "Variable",
            },  # Valid
            {
                "Date": "",
                "Merchant": "Store",
                "Amount": "€ 100",
                "Category": "Food",
                "Type": "Variable",
            },  # Empty date
            {
                "Date": "2024-05",
                "Merchant": "Store",
                "Amount": "€ 100",
                "Category": "Food",
                "Type": "Variable",
            },  # Valid
        ]

        is_valid, errors = validate_dataframe_structure(data, ExpenseRow)

        assert is_valid is False
        assert len(errors) == 2
        assert "Row 2:" in errors[0]
        assert "Row 4:" in errors[1]

    def test_empty_data(self):
        """Test validation with empty data."""
        data = []

        is_valid, errors = validate_dataframe_structure(data, ExpenseRow)

        assert is_valid is True
        assert len(errors) == 0

    def test_many_errors(self):
        """Test validation with many errors (tests error limiting)."""
        # Create 20 rows with invalid dates
        data = [
            {
                "Date": f"invalid-{i}",
                "Merchant": "Store",
                "Amount": f"€ {i}.000",
                "Category": "Food",
                "Type": "Variable",
            }
            for i in range(20)
        ]

        is_valid, errors = validate_dataframe_structure(data, ExpenseRow)

        assert is_valid is False
        assert len(errors) == 20  # All rows have errors
