"""
Tests for extended validators module (Assets, Liabilities, Incomes).

Tests Pydantic validation models for multi-index sheets with dynamic columns.
"""

import pytest
from pydantic import ValidationError

from app.core.validators import AssetRow, IncomeRow, LiabilityRow, validate_dataframe_structure


class TestAssetRow:
    """Tests for AssetRow validation model."""

    def test_valid_asset_row(self):
        """Test valid asset row with multi-index columns."""
        row = AssetRow(
            Date="2024-01",
            **{"('Cash', 'Checking')": "1000", "('Investments', 'Stocks')": "5000"},
        )
        assert row.Date == "2024-01"

    def test_valid_asset_row_with_currency_symbols(self):
        """Test valid asset row with currency symbols."""
        row = AssetRow(
            Date="2024-01",
            **{"('Cash', 'Savings')": "€ 2,500.50", "('Cash', 'Checking')": "$ 1,000.00"},
        )
        assert row.Date == "2024-01"

    def test_invalid_date_format(self):
        """Test invalid date format."""
        with pytest.raises(ValidationError) as exc_info:
            AssetRow(Date="01-2024", **{"('Cash', 'Checking')": "1000"})
        assert "Date must be in YYYY-MM format" in str(exc_info.value)

    def test_empty_date(self):
        """Test empty date raises error."""
        with pytest.raises(ValidationError) as exc_info:
            AssetRow(Date="", **{"('Cash', 'Checking')": "1000"})
        assert "Date cannot be empty" in str(exc_info.value)

    def test_date_with_whitespace(self):
        """Test date with whitespace is stripped."""
        row = AssetRow(Date="  2024-01  ", **{"('Cash', 'Checking')": "1000"})
        assert row.Date == "2024-01"

    def test_valid_monetary_values(self):
        """Test various valid monetary value formats."""
        row = AssetRow(
            Date="2024-01",
            **{
                "('Cash', 'Checking')": "1000",
                "('Cash', 'Savings')": "€ 2,500.50",
                "('Investments', 'Stocks')": "$ 10,000",
                "('Property', 'House')": "250000.00",
            },
        )
        assert row.Date == "2024-01"

    def test_invalid_monetary_value(self):
        """Test invalid monetary value (no digits)."""
        with pytest.raises(ValidationError) as exc_info:
            AssetRow(Date="2024-01", **{"('Cash', 'Checking')": "invalid"})
        assert "invalid value" in str(exc_info.value)

    def test_empty_monetary_value(self):
        """Test empty monetary value is allowed (NaN in spreadsheet)."""
        row = AssetRow(Date="2024-01", **{"('Cash', 'Checking')": ""})
        assert row.Date == "2024-01"

    def test_nan_monetary_value(self):
        """Test NaN monetary value is allowed."""
        row = AssetRow(
            Date="2024-01", **{"('Cash', 'Checking')": "1000", "('Cash', 'Savings')": "NaN"}
        )
        assert row.Date == "2024-01"

    def test_none_monetary_value(self):
        """Test None monetary value is allowed."""
        row = AssetRow(Date="2024-01", **{"('Cash', 'Checking')": None})
        assert row.Date == "2024-01"

    def test_only_date_column(self):
        """Test row with only Date column is valid."""
        row = AssetRow(Date="2024-01")
        assert row.Date == "2024-01"


class TestLiabilityRow:
    """Tests for LiabilityRow validation model."""

    def test_valid_liability_row(self):
        """Test valid liability row with multi-index columns."""
        row = LiabilityRow(
            Date="2024-01",
            **{"('Mortgage', '')": "250000", "('Loans', 'Car')": "15000"},
        )
        assert row.Date == "2024-01"

    def test_valid_liability_row_with_currency_symbols(self):
        """Test valid liability row with currency symbols."""
        row = LiabilityRow(
            Date="2024-01",
            **{"('Mortgage', '')": "€ 250,000.00", "('Loans', 'Student')": "$ 20,000"},
        )
        assert row.Date == "2024-01"

    def test_invalid_date_format(self):
        """Test invalid date format."""
        with pytest.raises(ValidationError) as exc_info:
            LiabilityRow(Date="01-2024", **{"('Mortgage', '')": "250000"})
        assert "Date must be in YYYY-MM format" in str(exc_info.value)

    def test_empty_date(self):
        """Test empty date raises error."""
        with pytest.raises(ValidationError) as exc_info:
            LiabilityRow(Date="", **{"('Mortgage', '')": "250000"})
        assert "Date cannot be empty" in str(exc_info.value)

    def test_date_with_whitespace(self):
        """Test date with whitespace is stripped."""
        row = LiabilityRow(Date="  2024-01  ", **{"('Mortgage', '')": "250000"})
        assert row.Date == "2024-01"

    def test_valid_monetary_values(self):
        """Test various valid monetary value formats."""
        row = LiabilityRow(
            Date="2024-01",
            **{
                "('Mortgage', '')": "250000",
                "('Loans', 'Car')": "€ 15,000.50",
                "('Loans', 'Student')": "$ 20,000",
                "('Credit Cards', 'Visa')": "1500.00",
            },
        )
        assert row.Date == "2024-01"

    def test_invalid_monetary_value(self):
        """Test invalid monetary value (no digits)."""
        with pytest.raises(ValidationError) as exc_info:
            LiabilityRow(Date="2024-01", **{"('Mortgage', '')": "invalid"})
        assert "invalid value" in str(exc_info.value)

    def test_empty_monetary_value(self):
        """Test empty monetary value is allowed (NaN in spreadsheet)."""
        row = LiabilityRow(Date="2024-01", **{"('Mortgage', '')": ""})
        assert row.Date == "2024-01"

    def test_nan_monetary_value(self):
        """Test NaN monetary value is allowed."""
        row = LiabilityRow(
            Date="2024-01", **{"('Mortgage', '')": "250000", "('Loans', 'Car')": "NaN"}
        )
        assert row.Date == "2024-01"

    def test_none_monetary_value(self):
        """Test None monetary value is allowed."""
        row = LiabilityRow(Date="2024-01", **{"('Mortgage', '')": None})
        assert row.Date == "2024-01"

    def test_only_date_column(self):
        """Test row with only Date column is valid."""
        row = LiabilityRow(Date="2024-01")
        assert row.Date == "2024-01"


class TestIncomeRow:
    """Tests for IncomeRow validation model."""

    def test_valid_income_row(self):
        """Test valid income row with multi-index columns."""
        row = IncomeRow(
            Date="2024-01",
            **{"('Salary', '')": "3000", "('Freelance', 'Project A')": "500"},
        )
        assert row.Date == "2024-01"

    def test_valid_income_row_with_currency_symbols(self):
        """Test valid income row with currency symbols."""
        row = IncomeRow(
            Date="2024-01",
            **{"('Salary', '')": "€ 3,000.00", "('Investments', 'Dividends')": "$ 150.50"},
        )
        assert row.Date == "2024-01"

    def test_invalid_date_format(self):
        """Test invalid date format."""
        with pytest.raises(ValidationError) as exc_info:
            IncomeRow(Date="01-2024", **{"('Salary', '')": "3000"})
        assert "Date must be in YYYY-MM format" in str(exc_info.value)

    def test_empty_date(self):
        """Test empty date raises error."""
        with pytest.raises(ValidationError) as exc_info:
            IncomeRow(Date="", **{"('Salary', '')": "3000"})
        assert "Date cannot be empty" in str(exc_info.value)

    def test_date_with_whitespace(self):
        """Test date with whitespace is stripped."""
        row = IncomeRow(Date="  2024-01  ", **{"('Salary', '')": "3000"})
        assert row.Date == "2024-01"

    def test_valid_monetary_values(self):
        """Test various valid monetary value formats."""
        row = IncomeRow(
            Date="2024-01",
            **{
                "('Salary', '')": "3000",
                "('Freelance', 'Project A')": "€ 500.00",
                "('Investments', 'Dividends')": "$ 150",
                "('Rental', 'Apartment')": "1200.50",
            },
        )
        assert row.Date == "2024-01"

    def test_invalid_monetary_value(self):
        """Test invalid monetary value (no digits)."""
        with pytest.raises(ValidationError) as exc_info:
            IncomeRow(Date="2024-01", **{"('Salary', '')": "invalid"})
        assert "invalid value" in str(exc_info.value)

    def test_empty_monetary_value(self):
        """Test empty monetary value is allowed (NaN in spreadsheet)."""
        row = IncomeRow(Date="2024-01", **{"('Salary', '')": ""})
        assert row.Date == "2024-01"

    def test_nan_monetary_value(self):
        """Test NaN monetary value is allowed."""
        row = IncomeRow(
            Date="2024-01", **{"('Salary', '')": "3000", "('Freelance', 'Project A')": "NaN"}
        )
        assert row.Date == "2024-01"

    def test_none_monetary_value(self):
        """Test None monetary value is allowed."""
        row = IncomeRow(Date="2024-01", **{"('Salary', '')": None})
        assert row.Date == "2024-01"

    def test_only_date_column(self):
        """Test row with only Date column is valid."""
        row = IncomeRow(Date="2024-01")
        assert row.Date == "2024-01"


class TestValidateDataframeStructureExtended:
    """Tests for validate_dataframe_structure with new models."""

    def test_valid_asset_data(self):
        """Test validation with valid asset rows."""
        data = [
            {
                "Date": "2024-01",
                "('Cash', 'Checking')": "1000",
                "('Investments', 'Stocks')": "5000",
            },
            {
                "Date": "2024-02",
                "('Cash', 'Checking')": "1200",
                "('Investments', 'Stocks')": "5500",
            },
        ]

        is_valid, errors = validate_dataframe_structure(data, AssetRow)

        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_asset_data(self):
        """Test validation with invalid asset rows."""
        data = [
            {"Date": "2024-01", "('Cash', 'Checking')": "1000"},
            {"Date": "invalid", "('Cash', 'Checking')": "1000"},
            {"Date": "2024-03", "('Cash', 'Checking')": "invalid_value"},
        ]

        is_valid, errors = validate_dataframe_structure(data, AssetRow)

        assert is_valid is False
        assert len(errors) == 2  # Row 2 (invalid date) and Row 3 (invalid value)
        assert "Row 2:" in errors[0]
        assert "Row 3:" in errors[1]

    def test_valid_liability_data(self):
        """Test validation with valid liability rows."""
        data = [
            {"Date": "2024-01", "('Mortgage', '')": "250000", "('Loans', 'Car')": "15000"},
            {"Date": "2024-02", "('Mortgage', '')": "248000", "('Loans', 'Car')": "14000"},
        ]

        is_valid, errors = validate_dataframe_structure(data, LiabilityRow)

        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_liability_data(self):
        """Test validation with invalid liability rows."""
        data = [
            {"Date": "2024-01", "('Mortgage', '')": "250000"},
            {"Date": "", "('Mortgage', '')": "250000"},
            {"Date": "2024-03", "('Mortgage', '')": "not_a_number"},
        ]

        is_valid, errors = validate_dataframe_structure(data, LiabilityRow)

        assert is_valid is False
        assert len(errors) == 2
        assert "Row 2:" in errors[0]
        assert "Row 3:" in errors[1]

    def test_valid_income_data(self):
        """Test validation with valid income rows."""
        data = [
            {"Date": "2024-01", "('Salary', '')": "3000", "('Freelance', 'Project A')": "500"},
            {"Date": "2024-02", "('Salary', '')": "3000", "('Freelance', 'Project A')": "600"},
        ]

        is_valid, errors = validate_dataframe_structure(data, IncomeRow)

        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_income_data(self):
        """Test validation with invalid income rows."""
        data = [
            {"Date": "2024-01", "('Salary', '')": "3000"},
            {"Date": "01-2024", "('Salary', '')": "3000"},
            {"Date": "2024-03", "('Salary', '')": "text_instead_of_number"},
        ]

        is_valid, errors = validate_dataframe_structure(data, IncomeRow)

        assert is_valid is False
        assert len(errors) == 2
        assert "Row 2:" in errors[0]
        assert "Row 3:" in errors[1]

    def test_asset_data_with_nan_values(self):
        """Test asset data with NaN/empty values is valid."""
        data = [
            {"Date": "2024-01", "('Cash', 'Checking')": "1000", "('Investments', 'Stocks')": ""},
            {"Date": "2024-02", "('Cash', 'Checking')": "1200", "('Investments', 'Stocks')": "NaN"},
            {"Date": "2024-03", "('Cash', 'Checking')": "1300", "('Investments', 'Stocks')": None},
        ]

        is_valid, errors = validate_dataframe_structure(data, AssetRow)

        assert is_valid is True
        assert len(errors) == 0

    def test_mixed_valid_and_invalid_rows(self):
        """Test validation with mix of valid and invalid asset rows."""
        data = [
            {"Date": "2024-01", "('Cash', 'Checking')": "1000"},  # Valid
            {"Date": "bad-date", "('Cash', 'Checking')": "1000"},  # Invalid date
            {"Date": "2024-03", "('Cash', 'Checking')": "1200"},  # Valid
            {"Date": "", "('Cash', 'Checking')": "1000"},  # Empty date
            {"Date": "2024-05", "('Cash', 'Checking')": "abc"},  # Invalid value
        ]

        is_valid, errors = validate_dataframe_structure(data, AssetRow)

        assert is_valid is False
        assert len(errors) == 3
        assert "Row 2:" in errors[0]
        assert "Row 4:" in errors[1]
        assert "Row 5:" in errors[2]

    def test_empty_data(self):
        """Test validation with empty data."""
        data = []

        is_valid, errors = validate_dataframe_structure(data, AssetRow)
        assert is_valid is True
        assert len(errors) == 0

        is_valid, errors = validate_dataframe_structure(data, LiabilityRow)
        assert is_valid is True
        assert len(errors) == 0

        is_valid, errors = validate_dataframe_structure(data, IncomeRow)
        assert is_valid is True
        assert len(errors) == 0
