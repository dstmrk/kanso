"""Tests for utility functions in app/services/utils.py"""

from app.services.utils import format_currency, format_percentage


class TestFormatCurrency:
    """Tests for format_currency function to ensure proper currency display."""

    def test_eur_format_with_space(self):
        """EUR should show symbol after number with space and dot for thousands."""
        result = format_currency(1234.56, "EUR")
        assert result == "1.235 €"
        assert " €" in result  # Space before symbol
        assert "." in result  # Dot as thousands separator

    def test_usd_format_with_space(self):
        """USD should show symbol before number with space and comma for thousands."""
        result = format_currency(1234.56, "USD")
        assert result == "$ 1,235"
        assert result.startswith("$ ")  # Symbol and space at start
        assert "," in result  # Comma as thousands separator

    def test_gbp_format_with_space(self):
        """GBP should show symbol before number with space and comma for thousands."""
        result = format_currency(1234.56, "GBP")
        assert result == "£ 1,235"
        assert result.startswith("£ ")  # Symbol and space at start
        assert "," in result  # Comma as thousands separator

    def test_chf_format_with_space(self):
        """CHF should show symbol after number with space and dot for thousands."""
        result = format_currency(1234.56, "CHF")
        assert result == "1.235 Fr"
        assert " Fr" in result  # Space before symbol
        assert "." in result  # Dot as thousands separator

    def test_jpy_format_with_space(self):
        """JPY should show symbol before number with space and comma for thousands."""
        result = format_currency(1234.56, "JPY")
        assert result == "¥ 1,235"
        assert result.startswith("¥ ")  # Symbol and space at start
        assert "," in result  # Comma as thousands separator

    def test_all_currencies_have_space(self):
        """All currencies should have space between symbol and number."""
        currencies = ["EUR", "USD", "GBP", "CHF", "JPY"]
        amount = 1000.0

        for currency in currencies:
            result = format_currency(amount, currency)
            # Check that there's a space either after first char (symbol before)
            # or before last 2-3 chars (symbol after)
            assert " " in result, f"{currency} should have space between symbol and number"

    def test_large_numbers_with_thousands_separator(self):
        """Large numbers should have proper thousands separators."""
        # EUR with dots
        assert format_currency(1234567.89, "EUR") == "1.234.568 €"

        # USD with commas
        assert format_currency(1234567.89, "USD") == "$ 1,234,568"

    def test_small_numbers(self):
        """Small numbers should format correctly without thousands separator."""
        assert format_currency(123.45, "EUR") == "123 €"
        assert format_currency(123.45, "USD") == "$ 123"

    def test_zero_amount(self):
        """Zero amount should format correctly."""
        assert format_currency(0.0, "EUR") == "0 €"
        assert format_currency(0.0, "USD") == "$ 0"

    def test_negative_amount(self):
        """Negative amounts should format correctly."""
        result_eur = format_currency(-1234.56, "EUR")
        result_usd = format_currency(-1234.56, "USD")

        assert "-" in result_eur
        assert "-" in result_usd


class TestFormatPercentage:
    """Tests for format_percentage function."""

    def test_eur_uses_comma_decimal(self):
        """EUR should use comma as decimal separator."""
        result = format_percentage(0.1234, "EUR")
        assert result == "12,34%"
        assert "," in result

    def test_usd_uses_dot_decimal(self):
        """USD should use dot as decimal separator."""
        result = format_percentage(0.1234, "USD")
        assert result == "12.34%"
        assert "." in result

    def test_gbp_uses_dot_decimal(self):
        """GBP should use dot as decimal separator."""
        result = format_percentage(0.1234, "GBP")
        assert result == "12.34%"
        assert "." in result

    def test_chf_uses_comma_decimal(self):
        """CHF should use comma as decimal separator."""
        result = format_percentage(0.1234, "CHF")
        assert result == "12,34%"
        assert "," in result
