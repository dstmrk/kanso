"""Unit tests for UI common utilities."""

from app.ui.common import get_aggrid_currency_formatter


class TestGetAggridCurrencyFormatter:
    """Test AG Grid currency formatter generator."""

    def test_eur_formatter(self):
        """EUR formatter should have symbol after, use de-DE locale, and use comma decimals."""
        formatter = get_aggrid_currency_formatter("EUR")

        # Should be valid JavaScript
        assert "value != null" in formatter
        assert "de-DE" in formatter
        assert "€" in formatter

        # Symbol should be after number
        assert "+ ' €'" in formatter

        # Should have decimals
        assert "minimumFractionDigits: 2" in formatter
        assert "maximumFractionDigits: 2" in formatter

    def test_usd_formatter(self):
        """USD formatter should have symbol before, use en-US locale, and use dot decimals."""
        formatter = get_aggrid_currency_formatter("USD")

        assert "en-US" in formatter
        assert "$" in formatter

        # Symbol should be before number
        assert "'$ ' +" in formatter

        # Should have decimals
        assert "minimumFractionDigits: 2" in formatter

    def test_gbp_formatter(self):
        """GBP formatter should have symbol before."""
        formatter = get_aggrid_currency_formatter("GBP")

        assert "en-GB" in formatter
        assert "£" in formatter
        assert "'£ ' +" in formatter

    def test_jpy_formatter_no_decimals(self):
        """JPY formatter should have no decimals."""
        formatter = get_aggrid_currency_formatter("JPY")

        assert "ja-JP" in formatter
        assert "¥" in formatter

        # Should NOT have decimal fractions
        assert "minimumFractionDigits" not in formatter
        assert "maximumFractionDigits: 0" in formatter

        # Null value should be just "0" without decimals
        assert "'0'" in formatter
        assert "'0.00'" not in formatter

    def test_chf_formatter(self):
        """CHF formatter should have symbol after and use comma decimals."""
        formatter = get_aggrid_currency_formatter("CHF")

        assert "de-CH" in formatter
        assert "Fr" in formatter
        assert "+ ' Fr'" in formatter

    def test_all_currencies_generate_formatter(self):
        """All supported currencies should generate valid formatter."""
        from app.core.currency_formats import get_supported_currencies

        for currency in get_supported_currencies():
            formatter = get_aggrid_currency_formatter(currency)

            # Should be non-empty string
            assert isinstance(formatter, str)
            assert len(formatter) > 0

            # Should contain value check
            assert "value != null" in formatter

            # Should contain toLocaleString
            assert "toLocaleString" in formatter

    def test_formatter_handles_null_values(self):
        """Formatter should have null value handling."""
        formatter = get_aggrid_currency_formatter("EUR")

        # Should have ternary operator for null handling
        assert "?" in formatter
        assert ":" in formatter

        # Should have null value fallback
        assert "value != null" in formatter

    def test_formatter_is_valid_javascript(self):
        """Formatter should be syntactically valid JavaScript."""
        formatter = get_aggrid_currency_formatter("USD")

        # Should have proper structure
        assert formatter.startswith("value != null")
        assert " ? " in formatter
        assert " : " in formatter

        # Should have balanced quotes
        single_quotes = formatter.count("'")
        assert single_quotes % 2 == 0  # Even number

    def test_symbol_position_before(self):
        """Currencies with 'before' position should format correctly."""
        # USD, GBP, JPY, CAD, AUD, CNY, INR have symbol before
        for currency in ["USD", "GBP", "JPY", "CAD", "AUD", "CNY", "INR"]:
            formatter = get_aggrid_currency_formatter(currency)

            # Check that symbol comes first in the format
            # Pattern: 'symbol ' + number
            assert " ' +" in formatter or "' +" in formatter

    def test_symbol_position_after(self):
        """Currencies with 'after' position should format correctly."""
        # Only EUR and CHF have symbol after
        for currency in ["EUR", "CHF"]:
            formatter = get_aggrid_currency_formatter(currency)

            # Check that number comes first
            # Pattern: number + ' symbol'
            assert "+ ' " in formatter

    def test_decimal_handling_consistency(self):
        """Currencies with decimals should all use 2 decimal places."""
        currencies_with_decimals = ["EUR", "USD", "GBP", "CHF", "CAD", "AUD", "CNY", "INR", "BRL"]

        for currency in currencies_with_decimals:
            formatter = get_aggrid_currency_formatter(currency)

            assert "minimumFractionDigits: 2" in formatter
            assert "maximumFractionDigits: 2" in formatter

    def test_jpy_special_case(self):
        """JPY is the only currency without decimals."""
        jpy_formatter = get_aggrid_currency_formatter("JPY")

        # No decimal fractions
        assert "minimumFractionDigits" not in jpy_formatter
        assert "maximumFractionDigits: 0" in jpy_formatter

        # All others should have decimals
        for currency in ["EUR", "USD", "GBP", "CHF", "CAD", "AUD", "CNY", "INR", "BRL"]:
            formatter = get_aggrid_currency_formatter(currency)
            assert "minimumFractionDigits: 2" in formatter
