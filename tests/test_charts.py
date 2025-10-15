"""Tests for chart formatting functions in app/ui/charts.py"""

from app.core.currency_formats import CURRENCY_FORMATS
from app.ui.charts import ChartOptionsBuilder


class TestCurrencySymbolMapping:
    """Tests for currency symbol mapping."""

    def test_currency_symbols_defined(self):
        """All supported currencies should have symbols defined in centralized config."""
        assert CURRENCY_FORMATS["EUR"].symbol == "€"
        assert CURRENCY_FORMATS["USD"].symbol == "$"
        assert CURRENCY_FORMATS["GBP"].symbol == "£"
        assert CURRENCY_FORMATS["CHF"].symbol == "Fr"
        assert CURRENCY_FORMATS["JPY"].symbol == "¥"

    def test_get_currency_symbol(self):
        """get_currency_symbol should return correct symbols."""
        assert ChartOptionsBuilder.get_currency_symbol("EUR") == "€"
        assert ChartOptionsBuilder.get_currency_symbol("USD") == "$"
        assert ChartOptionsBuilder.get_currency_symbol("GBP") == "£"
        assert ChartOptionsBuilder.get_currency_symbol("CHF") == "Fr"
        assert ChartOptionsBuilder.get_currency_symbol("JPY") == "¥"

    def test_get_currency_symbol_fallback(self):
        """get_currency_symbol should fallback to USD symbol for unknown currencies."""
        assert ChartOptionsBuilder.get_currency_symbol("XXX") == "$"


class TestCreateCurrencyFormatter:
    """Tests for create_currency_formatter function."""

    def test_eur_formatter_contains_symbol_and_space(self):
        """EUR formatter should contain € symbol and space."""
        formatter = ChartOptionsBuilder.create_currency_formatter("EUR", decimals=2)
        assert "€" in formatter
        assert '" €"' in formatter  # Space before symbol in JS string

    def test_usd_formatter_contains_symbol_and_space(self):
        """USD formatter should contain $ symbol and space."""
        formatter = ChartOptionsBuilder.create_currency_formatter("USD", decimals=2)
        assert "$" in formatter
        assert '"$ "' in formatter  # Space after symbol in JS string

    def test_gbp_formatter_contains_symbol_and_space(self):
        """GBP formatter should contain £ symbol and space."""
        formatter = ChartOptionsBuilder.create_currency_formatter("GBP", decimals=2)
        assert "£" in formatter
        assert '"£ "' in formatter  # Space after symbol in JS string

    def test_chf_formatter_contains_symbol_and_space(self):
        """CHF formatter should contain Fr symbol and space."""
        formatter = ChartOptionsBuilder.create_currency_formatter("CHF", decimals=2)
        assert "Fr" in formatter
        assert '" Fr"' in formatter  # Space before symbol in JS string

    def test_jpy_formatter_contains_symbol_and_space(self):
        """JPY formatter should contain ¥ symbol and space."""
        formatter = ChartOptionsBuilder.create_currency_formatter("JPY", decimals=0)
        assert "¥" in formatter
        assert '"¥ "' in formatter  # Space after symbol in JS string

    def test_all_formatters_have_space(self):
        """All currency formatters should have space between symbol and number."""
        currencies = ["EUR", "USD", "GBP", "CHF", "JPY"]

        for currency in currencies:
            formatter = ChartOptionsBuilder.create_currency_formatter(currency)
            # Check for space in the JS string (either '" €"' or '"$ "')
            has_space = '" ' in formatter or ' "' in formatter
            assert has_space, f"{currency} formatter should have space between symbol and number"

    def test_eur_formatter_uses_dot_separator(self):
        """EUR formatter should use dot as thousands separator."""
        formatter = ChartOptionsBuilder.create_currency_formatter("EUR", decimals=2)
        # Check that the formatter uses dot for thousands (replace with ".")
        assert '\\B(?=(\\d{3})+(?!\\d))/g, "."' in formatter

    def test_usd_formatter_uses_comma_separator(self):
        """USD formatter should use comma as thousands separator."""
        formatter = ChartOptionsBuilder.create_currency_formatter("USD", decimals=2)
        # Check that the formatter uses comma for thousands (replace with ",")
        assert '\\B(?=(\\d{3})+(?!\\d))/g, ","' in formatter

    def test_jpy_formatter_no_decimals(self):
        """JPY formatter should not have decimal places."""
        formatter = ChartOptionsBuilder.create_currency_formatter("JPY", decimals=0)
        # JPY should use toFixed(0) - no decimals
        assert "toFixed(0)" in formatter
        # Should not split on decimal point (no decimal handling)
        assert 'split(".")' not in formatter

    def test_formatter_with_decimals(self):
        """Formatter with decimals should split and handle decimal part."""
        formatter = ChartOptionsBuilder.create_currency_formatter("USD", decimals=2)
        # Should use toFixed(2) and split on "."
        assert "toFixed(2)" in formatter
        assert 'split(".")' in formatter

    def test_formatter_without_decimals(self):
        """Formatter without decimals should use toFixed(0)."""
        formatter = ChartOptionsBuilder.create_currency_formatter("USD", decimals=0)
        assert "toFixed(0)" in formatter

    def test_formatter_is_valid_javascript_function(self):
        """Generated formatter should be a valid JavaScript function string."""
        formatter = ChartOptionsBuilder.create_currency_formatter("USD", decimals=2)
        # Should start with function keyword
        assert formatter.startswith("function(")
        # Should have opening and closing braces
        assert "{" in formatter
        assert "}" in formatter
        # Should have return statement
        assert "return" in formatter


class TestGetCommonTooltip:
    """Tests for get_common_tooltip function."""

    def test_tooltip_has_value_formatter(self):
        """Tooltip should have :valueFormatter key."""
        tooltip = ChartOptionsBuilder.get_common_tooltip("USD")
        assert ":valueFormatter" in tooltip

    def test_tooltip_formatter_is_function(self):
        """Tooltip formatter should be a JavaScript function."""
        tooltip = ChartOptionsBuilder.get_common_tooltip("USD")
        formatter = tooltip[":valueFormatter"]
        assert formatter.startswith("function(")

    def test_tooltip_uses_correct_currency(self):
        """Tooltip should use the specified currency symbol."""
        tooltip_usd = ChartOptionsBuilder.get_common_tooltip("USD")
        tooltip_eur = ChartOptionsBuilder.get_common_tooltip("EUR")

        assert "$" in tooltip_usd[":valueFormatter"]
        assert "€" in tooltip_eur[":valueFormatter"]


class TestGetCurrencyAxisLabel:
    """Tests for get_currency_axis_label function."""

    def test_axis_label_has_formatter(self):
        """Axis label should have :formatter key."""
        label = ChartOptionsBuilder.get_currency_axis_label("desktop", "USD")
        assert ":formatter" in label

    def test_axis_label_has_font_size(self):
        """Axis label should have fontSize key."""
        label = ChartOptionsBuilder.get_currency_axis_label("desktop", "USD")
        assert "fontSize" in label

    def test_axis_label_font_size_varies_by_device(self):
        """Axis label font size should vary by device type."""
        desktop_label = ChartOptionsBuilder.get_currency_axis_label("desktop", "USD")
        mobile_label = ChartOptionsBuilder.get_currency_axis_label("mobile", "USD")

        assert desktop_label["fontSize"] == 12
        assert mobile_label["fontSize"] == 8

    def test_axis_label_uses_no_decimals(self):
        """Axis label should use 0 decimals (integers only)."""
        label = ChartOptionsBuilder.get_currency_axis_label("desktop", "USD")
        formatter = label[":formatter"]
        # Should use decimals=0 which means toFixed(0)
        assert "toFixed(0)" in formatter

    def test_axis_label_uses_correct_currency(self):
        """Axis label should use the specified currency symbol."""
        label_usd = ChartOptionsBuilder.get_currency_axis_label("desktop", "USD")
        label_eur = ChartOptionsBuilder.get_currency_axis_label("desktop", "EUR")

        assert "$" in label_usd[":formatter"]
        assert "€" in label_eur[":formatter"]
