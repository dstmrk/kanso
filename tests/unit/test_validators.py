"""
Tests for validators module.

Tests Pydantic validation models for expenses sheet.
"""

import json

import pytest
from pydantic import ValidationError

from app.core.validators import (
    ExpenseRow,
    clean_google_sheets_url,
    validate_credentials_and_url,
    validate_dataframe_structure,
    validate_google_credentials_json,
    validate_google_sheets_url,
)


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


class TestCleanGoogleSheetsUrl:
    """Tests for clean_google_sheets_url function."""

    def test_clean_url_with_query_params(self):
        """Should remove query parameters from URL."""
        url = "https://docs.google.com/spreadsheets/d/ABC123/edit?usp=sharing"
        cleaned = clean_google_sheets_url(url)
        assert cleaned == "https://docs.google.com/spreadsheets/d/ABC123/edit"

    def test_clean_url_with_gid_param(self):
        """Should remove gid parameter from URL."""
        url = "https://docs.google.com/spreadsheets/d/ABC123/edit#gid=0"
        cleaned = clean_google_sheets_url(url)
        assert cleaned == "https://docs.google.com/spreadsheets/d/ABC123/edit"

    def test_clean_url_already_clean(self):
        """Should return same URL if already clean."""
        url = "https://docs.google.com/spreadsheets/d/ABC123/edit"
        cleaned = clean_google_sheets_url(url)
        assert cleaned == url

    def test_clean_url_with_copy_suffix(self):
        """Should handle URLs with /copy suffix."""
        url = "https://docs.google.com/spreadsheets/d/ABC123/copy"
        cleaned = clean_google_sheets_url(url)
        assert cleaned == "https://docs.google.com/spreadsheets/d/ABC123/edit"

    def test_clean_url_with_view_suffix(self):
        """Should handle URLs with /view suffix."""
        url = "https://docs.google.com/spreadsheets/d/ABC123/view"
        cleaned = clean_google_sheets_url(url)
        assert cleaned == "https://docs.google.com/spreadsheets/d/ABC123/edit"

    def test_clean_url_invalid_format(self):
        """Should raise ValueError for invalid URL format."""
        with pytest.raises(ValueError, match="Could not extract workbook ID"):
            clean_google_sheets_url("https://example.com/not-a-spreadsheet")

    def test_clean_url_with_underscores_and_hyphens(self):
        """Should handle workbook IDs with underscores and hyphens."""
        url = "https://docs.google.com/spreadsheets/d/ABC-123_DEF/edit"
        cleaned = clean_google_sheets_url(url)
        assert cleaned == "https://docs.google.com/spreadsheets/d/ABC-123_DEF/edit"


class TestValidateGoogleSheetsUrl:
    """Tests for validate_google_sheets_url function."""

    def test_valid_url(self):
        """Should validate correct Google Sheets URL."""
        url = "https://docs.google.com/spreadsheets/d/ABC123/edit"
        is_valid, error = validate_google_sheets_url(url)
        assert is_valid is True
        assert error == ""

    def test_valid_url_with_params(self):
        """Should validate URL with query parameters."""
        url = "https://docs.google.com/spreadsheets/d/ABC123/edit?usp=sharing"
        is_valid, error = validate_google_sheets_url(url)
        assert is_valid is True
        assert error == ""

    def test_empty_url(self):
        """Should reject empty URL."""
        is_valid, error = validate_google_sheets_url("")
        assert is_valid is False
        assert error == "URL is required"

    def test_none_url(self):
        """Should reject None URL."""
        is_valid, error = validate_google_sheets_url(None)
        assert is_valid is False
        assert error == "URL is required"

    def test_non_google_url(self):
        """Should reject non-Google URLs."""
        url = "https://example.com/spreadsheet"
        is_valid, error = validate_google_sheets_url(url)
        assert is_valid is False
        assert error == "Invalid Google Sheets URL format"

    def test_google_docs_url(self):
        """Should reject Google Docs URLs (not Sheets)."""
        url = "https://docs.google.com/document/d/ABC123/edit"
        is_valid, error = validate_google_sheets_url(url)
        assert is_valid is False
        assert error == "Invalid Google Sheets URL format"

    def test_url_without_workbook_id(self):
        """Should reject URL without workbook ID."""
        url = "https://docs.google.com/spreadsheets/"
        is_valid, error = validate_google_sheets_url(url)
        assert is_valid is False
        assert "Could not find workbook ID" in error


class TestValidateGoogleCredentialsJson:
    """Tests for validate_google_credentials_json function."""

    def test_valid_credentials(self):
        """Should validate correct service account credentials."""
        credentials = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key123",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
        }
        is_valid, result = validate_google_credentials_json(json.dumps(credentials))
        assert is_valid is True
        assert result == credentials

    def test_empty_json(self):
        """Should reject empty JSON string."""
        is_valid, error = validate_google_credentials_json("")
        assert is_valid is False
        assert error == "Credentials JSON is required"

    def test_none_json(self):
        """Should reject None."""
        is_valid, error = validate_google_credentials_json(None)
        assert is_valid is False
        assert error == "Credentials JSON is required"

    def test_invalid_json_format(self):
        """Should reject malformed JSON."""
        is_valid, error = validate_google_credentials_json("not valid json")
        assert is_valid is False
        assert "Invalid JSON format" in error

    def test_json_array_not_object(self):
        """Should reject JSON array instead of object."""
        is_valid, error = validate_google_credentials_json("[1, 2, 3]")
        assert is_valid is False
        assert "must be an object" in error

    def test_missing_type_field(self):
        """Should reject credentials without 'type' field."""
        credentials = {"project_id": "test-project"}
        is_valid, error = validate_google_credentials_json(json.dumps(credentials))
        assert is_valid is False
        assert "Missing 'type' field" in error

    def test_invalid_type_value(self):
        """Should reject non-service_account type."""
        credentials = {"type": "user_account", "project_id": "test"}
        is_valid, error = validate_google_credentials_json(json.dumps(credentials))
        assert is_valid is False
        assert "Invalid credential type" in error
        assert "service_account" in error

    def test_missing_required_fields(self):
        """Should reject credentials missing required fields."""
        credentials = {
            "type": "service_account",
            "project_id": "test-project",
            # Missing: private_key_id, private_key, client_email
        }
        is_valid, error = validate_google_credentials_json(json.dumps(credentials))
        assert is_valid is False
        assert "Missing required fields" in error
        assert "private_key_id" in error

    def test_missing_multiple_fields(self):
        """Should list all missing required fields."""
        credentials = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key123",
            # Missing: private_key, client_email
        }
        is_valid, error = validate_google_credentials_json(json.dumps(credentials))
        assert is_valid is False
        assert "private_key" in error
        assert "client_email" in error


class TestValidateCredentialsAndUrl:
    """Tests for validate_credentials_and_url combined validator."""

    VALID_CREDS = json.dumps(
        {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key123",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----\n",
            "client_email": "test@test.iam.gserviceaccount.com",
        }
    )
    VALID_URL = "https://docs.google.com/spreadsheets/d/abc123/edit"

    def test_valid_credentials_and_url(self):
        """Both valid credentials and URL should return success with cleaned URL."""
        is_valid, result, clean_url = validate_credentials_and_url(self.VALID_CREDS, self.VALID_URL)
        assert is_valid is True
        assert isinstance(result, dict)
        assert "abc123" in clean_url

    def test_invalid_credentials(self):
        """Invalid credentials should return error."""
        is_valid, error, clean_url = validate_credentials_and_url("not json", self.VALID_URL)
        assert is_valid is False
        assert "Invalid JSON" in error
        assert clean_url is None

    def test_invalid_url(self):
        """Invalid URL with valid credentials should return URL error."""
        is_valid, error, clean_url = validate_credentials_and_url(self.VALID_CREDS, "not-a-url")
        assert is_valid is False
        assert clean_url is None

    def test_empty_credentials(self):
        """Empty credentials should return error."""
        is_valid, error, clean_url = validate_credentials_and_url("", self.VALID_URL)
        assert is_valid is False
        assert clean_url is None
