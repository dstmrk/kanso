"""Unit tests for monetary parsing utilities.

Tests the monetary_parsing module's currency detection and value parsing
functions with comprehensive edge cases and error scenarios.
"""

import pytest

from app.logic.monetary_parsing import detect_currency, parse_monetary_value


class TestDetectCurrency:
    """Tests for currency detection from symbols."""

    def test_detect_eur_symbol(self):
        """Test detecting EUR from € symbol."""
        assert detect_currency("€ 1.234,56") == "EUR"
        assert detect_currency("1.234,56 €") == "EUR"
        assert detect_currency("€1234") == "EUR"

    def test_detect_usd_symbol(self):
        """Test detecting USD from $ symbol."""
        assert detect_currency("$1,234.56") == "USD"
        assert detect_currency("1,234.56 $") == "USD"
        assert detect_currency("$1234") == "USD"

    def test_detect_gbp_symbol(self):
        """Test detecting GBP from £ symbol."""
        assert detect_currency("£1,234.56") == "GBP"
        assert detect_currency("1,234.56 £") == "GBP"

    def test_detect_chf_text(self):
        """Test detecting CHF from text."""
        assert detect_currency("1'234.56 CHF") == "CHF"
        assert detect_currency("CHF 1234") == "CHF"
        assert detect_currency("Fr 1234") == "CHF"

    def test_detect_jpy_text(self):
        """Test detecting JPY from text."""
        assert detect_currency("¥1,234") == "JPY"
        assert detect_currency("1234 JPY") == "JPY"

    def test_detect_none_no_symbol(self):
        """Test that None is returned when no currency symbol found."""
        assert detect_currency("1234.56") is None
        assert detect_currency("1,234") is None
        assert detect_currency("plain text") is None

    def test_detect_empty_string(self):
        """Test detection with empty string."""
        assert detect_currency("") is None
        assert detect_currency("   ") is None


class TestParseMonetaryValue:
    """Tests for monetary value parsing with multi-currency support."""

    # European format tests (EUR, CHF)
    def test_parse_european_format_eur(self):
        """Test parsing European format (1.234,56) with EUR."""
        assert parse_monetary_value("€ 1.234,56") == pytest.approx(1234.56)
        assert parse_monetary_value("€ 1.000,00") == pytest.approx(1000.0)
        assert parse_monetary_value("€ 999,99") == pytest.approx(999.99)

    def test_parse_european_format_chf(self):
        """Test parsing Swiss format with CHF."""
        # CHF uses European format (comma for decimals), spaces for thousands
        assert parse_monetary_value("Fr 1 234,56") == pytest.approx(1234.56)
        assert parse_monetary_value("CHF 1000") == pytest.approx(1000.0)
        assert parse_monetary_value("Fr 1.234,56") == pytest.approx(
            1234.56
        )  # Dot as thousands separator

    # US/UK format tests (USD, GBP)
    def test_parse_us_format_usd(self):
        """Test parsing US format (1,234.56) with USD."""
        assert parse_monetary_value("$1,234.56") == pytest.approx(1234.56)
        assert parse_monetary_value("$ 1,000.00") == pytest.approx(1000.0)
        assert parse_monetary_value("$999.99") == pytest.approx(999.99)

    def test_parse_uk_format_gbp(self):
        """Test parsing UK format with GBP."""
        assert parse_monetary_value("£1,234.56") == pytest.approx(1234.56)
        assert parse_monetary_value("£ 1,000.00") == pytest.approx(1000.0)

    # Japanese format tests (no decimals)
    def test_parse_japanese_format_jpy(self):
        """Test parsing Japanese format (no decimals) with JPY."""
        assert parse_monetary_value("¥1,234") == pytest.approx(1234.0)
        assert parse_monetary_value("JPY 1234") == pytest.approx(1234.0)

    # Plain number tests (no currency symbol)
    def test_parse_plain_number_single_dot(self):
        """Test parsing plain number with single dot (decimal)."""
        assert parse_monetary_value("1234.56") == pytest.approx(1234.56)
        assert parse_monetary_value("999.99") == pytest.approx(999.99)

    def test_parse_plain_number_single_comma(self):
        """Test parsing plain number with single comma (European decimal)."""
        assert parse_monetary_value("1234,56") == pytest.approx(1234.56)
        assert parse_monetary_value("999,99") == pytest.approx(999.99)

    def test_parse_plain_number_no_separator(self):
        """Test parsing plain integer without separators."""
        assert parse_monetary_value("1234") == pytest.approx(1234.0)
        assert parse_monetary_value("5000") == pytest.approx(5000.0)

    def test_parse_plain_number_multiple_separators(self):
        """Test plain numbers with multiple separators default to EUR format."""
        # When no currency detected, falls back to EUR format
        assert parse_monetary_value("1.234,56") == pytest.approx(1234.56)

    # Whitespace handling
    def test_parse_with_spaces(self):
        """Test parsing with various whitespace."""
        assert parse_monetary_value("€ 1 234,56") == pytest.approx(1234.56)
        assert parse_monetary_value("$ 1 234.56") == pytest.approx(1234.56)
        assert parse_monetary_value("  €  1234  ") == pytest.approx(1234.0)

    # Currency override tests
    def test_parse_with_currency_override(self):
        """Test parsing with explicit currency override."""
        # Force EUR interpretation (dot = thousands)
        assert parse_monetary_value("1.234,56", currency="EUR") == pytest.approx(1234.56)
        # Force USD interpretation (dot = decimal)
        assert parse_monetary_value("1234.56", currency="USD") == pytest.approx(1234.56)

    # Numeric type inputs
    def test_parse_numeric_types(self):
        """Test parsing int and float inputs."""
        assert parse_monetary_value(1234) == pytest.approx(1234.0)
        assert parse_monetary_value(1234.56) == pytest.approx(1234.56)
        assert parse_monetary_value(0) == pytest.approx(0.0)

    # None and empty string handling
    def test_parse_none(self):
        """Test parsing None returns 0.0."""
        assert parse_monetary_value(None) == pytest.approx(0.0)

    def test_parse_empty_string(self):
        """Test parsing empty string returns 0.0."""
        assert parse_monetary_value("") == pytest.approx(0.0)
        assert parse_monetary_value("   ") == pytest.approx(0.0)

    def test_parse_dash_only(self):
        """Test parsing dash (common in Google Sheets for zero) returns 0.0."""
        assert parse_monetary_value("-") == pytest.approx(0.0)
        assert parse_monetary_value(" - ") == pytest.approx(0.0)

    # Invalid format tests
    def test_parse_text_only(self):
        """Test parsing text-only values returns 0.0 (with warning logged)."""
        assert parse_monetary_value("abc") == pytest.approx(0.0)
        assert parse_monetary_value("Total") == pytest.approx(0.0)

    def test_parse_invalid_mixed_format(self):
        """Test parsing invalid mixed formats returns 0.0."""
        assert parse_monetary_value("€€€") == pytest.approx(0.0)
        assert parse_monetary_value("abc123xyz") == pytest.approx(0.0)

    # Large number tests
    def test_parse_large_numbers(self):
        """Test parsing large monetary values."""
        assert parse_monetary_value("€ 1.234.567,89") == pytest.approx(1234567.89)
        assert parse_monetary_value("$1,234,567.89") == pytest.approx(1234567.89)
        assert parse_monetary_value("¥12,345,678") == pytest.approx(12345678.0)

    # Negative numbers
    def test_parse_negative_numbers(self):
        """Test parsing negative monetary values."""
        # Note: Most formats strip the minus, but the float conversion handles it
        assert parse_monetary_value("€ -1.234,56") == pytest.approx(-1234.56)
        assert parse_monetary_value("$-1,234.56") == pytest.approx(-1234.56)

    # Mixed formats in same value (edge case)
    def test_parse_ambiguous_format(self):
        """Test handling of ambiguous formats (relies on currency detection)."""
        # With EUR symbol, should use European format
        assert parse_monetary_value("€ 1.234") == pytest.approx(1234.0)  # dot = thousands
        # With USD symbol, should use US format
        assert parse_monetary_value("$ 1,234") == pytest.approx(1234.0)  # comma = thousands

    # Zero values
    def test_parse_zero_values(self):
        """Test parsing various representations of zero."""
        assert parse_monetary_value("€ 0") == pytest.approx(0.0)
        assert parse_monetary_value("€ 0,00") == pytest.approx(0.0)
        assert parse_monetary_value("$0.00") == pytest.approx(0.0)
        assert parse_monetary_value("0") == pytest.approx(0.0)


class TestParseMonetaryValueEdgeCases:
    """Additional edge case tests for parse_monetary_value."""

    def test_parse_very_small_decimals(self):
        """Test parsing very small decimal values."""
        assert parse_monetary_value("€ 0,01") == pytest.approx(0.01)
        assert parse_monetary_value("$0.01") == pytest.approx(0.01)

    def test_parse_no_whole_part(self):
        """Test parsing values with no whole number part."""
        assert parse_monetary_value("€ ,50") == pytest.approx(0.50)
        assert parse_monetary_value("$.50") == pytest.approx(0.50)

    def test_parse_trailing_zeros(self):
        """Test parsing with trailing zeros."""
        assert parse_monetary_value("€ 100,00") == pytest.approx(100.0)
        assert parse_monetary_value("$100.00") == pytest.approx(100.0)

    def test_parse_leading_zeros(self):
        """Test parsing with leading zeros."""
        assert parse_monetary_value("€ 0.100") == pytest.approx(100.0)  # European: dot = thousands
        assert parse_monetary_value("$0001234.56") == pytest.approx(1234.56)

    def test_parse_multiple_currency_symbols(self):
        """Test handling of multiple currency symbols (should detect first)."""
        # Should detect EUR from € symbol
        assert detect_currency("€ $ 100") == "EUR"
        # Should still parse correctly
        assert parse_monetary_value("€ $ 100") == pytest.approx(100.0)
