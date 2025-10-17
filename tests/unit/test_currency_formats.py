"""Tests for centralized currency configuration in app/core/currency_formats.py"""

from app.core.currency_formats import (
    CURRENCY_FORMATS,
    CurrencyFormat,
    get_currency_format,
    get_currency_symbol,
    get_supported_currencies,
)


class TestCurrencyFormats:
    """Tests for CURRENCY_FORMATS configuration."""

    def test_all_currencies_defined(self):
        """All required currencies should be defined."""
        assert "EUR" in CURRENCY_FORMATS
        assert "USD" in CURRENCY_FORMATS
        assert "GBP" in CURRENCY_FORMATS
        assert "CHF" in CURRENCY_FORMATS
        assert "JPY" in CURRENCY_FORMATS

    def test_currency_format_is_frozen(self):
        """CurrencyFormat instances should be immutable (frozen)."""
        fmt = CURRENCY_FORMATS["EUR"]
        try:
            fmt.symbol = "X"
            raise AssertionError("Should not be able to modify frozen dataclass")
        except (AttributeError, TypeError):
            pass  # Expected behavior - frozen dataclass raises AttributeError

    def test_eur_format(self):
        """EUR should have correct formatting configuration."""
        fmt = CURRENCY_FORMATS["EUR"]
        assert fmt.symbol == "€"
        assert fmt.position == "after"
        assert fmt.thousands_sep == "."
        assert fmt.decimal_sep == ","
        assert fmt.has_decimals is True

    def test_usd_format(self):
        """USD should have correct formatting configuration."""
        fmt = CURRENCY_FORMATS["USD"]
        assert fmt.symbol == "$"
        assert fmt.position == "before"
        assert fmt.thousands_sep == ","
        assert fmt.decimal_sep == "."
        assert fmt.has_decimals is True

    def test_gbp_format(self):
        """GBP should have correct formatting configuration."""
        fmt = CURRENCY_FORMATS["GBP"]
        assert fmt.symbol == "£"
        assert fmt.position == "before"
        assert fmt.thousands_sep == ","
        assert fmt.decimal_sep == "."
        assert fmt.has_decimals is True

    def test_chf_format(self):
        """CHF should have correct formatting configuration."""
        fmt = CURRENCY_FORMATS["CHF"]
        assert fmt.symbol == "Fr"
        assert fmt.position == "after"
        assert fmt.thousands_sep == "."
        assert fmt.decimal_sep == ","
        assert fmt.has_decimals is True

    def test_jpy_format(self):
        """JPY should have correct formatting configuration (no decimals)."""
        fmt = CURRENCY_FORMATS["JPY"]
        assert fmt.symbol == "¥"
        assert fmt.position == "before"
        assert fmt.thousands_sep == ","
        assert fmt.decimal_sep == ""
        assert fmt.has_decimals is False


class TestGetCurrencyFormat:
    """Tests for get_currency_format function."""

    def test_get_existing_currency(self):
        """Should return correct format for existing currency."""
        fmt = get_currency_format("EUR")
        assert isinstance(fmt, CurrencyFormat)
        assert fmt.symbol == "€"

    def test_get_all_currencies(self):
        """Should be able to get all supported currencies."""
        for code in ["EUR", "USD", "GBP", "CHF", "JPY"]:
            fmt = get_currency_format(code)
            assert isinstance(fmt, CurrencyFormat)

    def test_get_unknown_currency_raises_error(self):
        """Should raise KeyError for unknown currency."""
        try:
            get_currency_format("XXX")
            raise AssertionError("Should raise KeyError for unknown currency")
        except KeyError:
            pass  # Expected behavior


class TestGetCurrencySymbol:
    """Tests for get_currency_symbol function."""

    def test_get_all_symbols(self):
        """Should return correct symbols for all currencies."""
        assert get_currency_symbol("EUR") == "€"
        assert get_currency_symbol("USD") == "$"
        assert get_currency_symbol("GBP") == "£"
        assert get_currency_symbol("CHF") == "Fr"
        assert get_currency_symbol("JPY") == "¥"

    def test_unknown_currency_fallback(self):
        """Should fallback to USD symbol for unknown currencies."""
        assert get_currency_symbol("XXX") == "$"


class TestGetSupportedCurrencies:
    """Tests for get_supported_currencies function."""

    def test_returns_list(self):
        """Should return a list of currency codes."""
        currencies = get_supported_currencies()
        assert isinstance(currencies, list)

    def test_contains_all_currencies(self):
        """Should contain all supported currency codes."""
        currencies = get_supported_currencies()
        assert "EUR" in currencies
        assert "USD" in currencies
        assert "GBP" in currencies
        assert "CHF" in currencies
        assert "JPY" in currencies

    def test_returns_five_currencies(self):
        """Should return exactly 5 supported currencies."""
        currencies = get_supported_currencies()
        assert len(currencies) == 5
