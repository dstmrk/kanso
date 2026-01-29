"""Tests for utility functions in app/services/utils.py"""

from datetime import UTC, datetime, timedelta

from app.services.utils import (
    format_currency,
    format_percentage,
    format_timestamp_relative,
    get_currency_from_browser_locale,
    get_current_timestamp,
)


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


class TestGetCurrentTimestamp:
    """Tests for get_current_timestamp function."""

    def test_returns_iso_8601_format(self):
        """Should return timestamp in ISO 8601 format with Z suffix."""
        timestamp = get_current_timestamp()

        # Check format: YYYY-MM-DDTHH:MM:SSZ
        assert len(timestamp) == 20
        assert timestamp[4] == "-"
        assert timestamp[7] == "-"
        assert timestamp[10] == "T"
        assert timestamp[13] == ":"
        assert timestamp[16] == ":"
        assert timestamp.endswith("Z")

    def test_returns_utc_time(self):
        """Should return UTC time (ending with Z)."""
        timestamp = get_current_timestamp()
        assert timestamp.endswith("Z")

    def test_returns_valid_datetime_string(self):
        """Should return a string that can be parsed back to datetime."""
        timestamp = get_current_timestamp()

        # Should be parseable
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert isinstance(parsed, datetime)
        assert parsed.tzinfo is not None

    def test_is_recent_timestamp(self):
        """Should return a timestamp close to current time."""
        timestamp = get_current_timestamp()
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(UTC)

        # Should be within 2 seconds of current time (allow for CI slowness)
        diff = abs((now - parsed).total_seconds())
        assert diff < 2.0


class TestFormatTimestampRelative:
    """Tests for format_timestamp_relative function."""

    def test_none_returns_never(self):
        """None timestamp should return 'Never' with empty relative time."""
        formatted, relative = format_timestamp_relative(None)
        assert formatted == "Never"
        assert relative == ""

    def test_empty_string_returns_never(self):
        """Empty string should return 'Never' with empty relative time."""
        formatted, relative = format_timestamp_relative("")
        assert formatted == "Never"
        assert relative == ""

    def test_just_now(self):
        """Timestamp within 60 seconds should show 'just now'."""
        # 30 seconds ago
        now = datetime.now(UTC)
        timestamp = (now - timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

        formatted, relative = format_timestamp_relative(timestamp)
        assert relative == "just now"
        assert formatted.startswith(str(now.year))

    def test_minutes_ago(self):
        """Timestamp within an hour should show minutes."""
        # 5 minutes ago
        now = datetime.now(UTC)
        timestamp = (now - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")

        _, relative = format_timestamp_relative(timestamp)
        assert "minute" in relative
        assert "ago" in relative

    def test_single_minute_ago(self):
        """1 minute ago should use singular 'minute'."""
        now = datetime.now(UTC)
        timestamp = (now - timedelta(minutes=1, seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

        _, relative = format_timestamp_relative(timestamp)
        assert relative == "1 minute ago"

    def test_multiple_minutes_ago(self):
        """Multiple minutes should use plural 'minutes'."""
        now = datetime.now(UTC)
        timestamp = (now - timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ")

        _, relative = format_timestamp_relative(timestamp)
        assert "minutes ago" in relative

    def test_hours_ago(self):
        """Timestamp within a day should show hours."""
        now = datetime.now(UTC)
        timestamp = (now - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")

        _, relative = format_timestamp_relative(timestamp)
        assert "hour" in relative
        assert "ago" in relative

    def test_single_hour_ago(self):
        """1 hour ago should use singular 'hour'."""
        now = datetime.now(UTC)
        timestamp = (now - timedelta(hours=1, minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

        _, relative = format_timestamp_relative(timestamp)
        assert relative == "1 hour ago"

    def test_days_ago(self):
        """Timestamp within a week should show days."""
        now = datetime.now(UTC)
        timestamp = (now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")

        _, relative = format_timestamp_relative(timestamp)
        assert "day" in relative
        assert "ago" in relative

    def test_single_day_ago(self):
        """1 day ago should use singular 'day'."""
        now = datetime.now(UTC)
        timestamp = (now - timedelta(days=1, hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")

        _, relative = format_timestamp_relative(timestamp)
        assert relative == "1 day ago"

    def test_weeks_ago(self):
        """Timestamp within a month should show weeks."""
        now = datetime.now(UTC)
        timestamp = (now - timedelta(weeks=2)).strftime("%Y-%m-%dT%H:%M:%SZ")

        _, relative = format_timestamp_relative(timestamp)
        assert "week" in relative
        assert "ago" in relative

    def test_months_ago(self):
        """Timestamp over a month should show months."""
        now = datetime.now(UTC)
        timestamp = (now - timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%SZ")

        _, relative = format_timestamp_relative(timestamp)
        assert "month" in relative
        assert "ago" in relative

    def test_formatted_absolute_time(self):
        """Should return formatted absolute time in YYYY-MM-DD HH:MM:SS format."""
        timestamp = "2025-10-18T14:30:45Z"
        formatted, _ = format_timestamp_relative(timestamp)

        # Check format
        assert formatted == "2025-10-18 14:30:45"
        assert len(formatted) == 19

    def test_invalid_timestamp_format(self):
        """Invalid timestamp should return 'Invalid timestamp'."""
        formatted, relative = format_timestamp_relative("not-a-timestamp")
        assert formatted == "Invalid timestamp"
        assert relative == ""


class TestInferCurrencyFromLocale:
    """Tests for get_currency_from_browser_locale function."""

    def test_none_locale_returns_usd(self):
        """None locale should return USD as default."""
        assert get_currency_from_browser_locale(None) == "USD"

    def test_empty_string_returns_usd(self):
        """Empty string locale should return USD as default."""
        assert get_currency_from_browser_locale("") == "USD"

    def test_en_us_returns_usd(self):
        """en-US locale should return USD."""
        assert get_currency_from_browser_locale("en-US") == "USD"

    def test_en_gb_returns_gbp(self):
        """en-GB locale should return GBP."""
        assert get_currency_from_browser_locale("en-GB") == "GBP"

    def test_en_ca_returns_cad(self):
        """en-CA locale should return CAD."""
        assert get_currency_from_browser_locale("en-CA") == "CAD"

    def test_en_au_returns_aud(self):
        """en-AU locale should return AUD."""
        assert get_currency_from_browser_locale("en-AU") == "AUD"

    def test_en_in_returns_inr(self):
        """en-IN locale should return INR."""
        assert get_currency_from_browser_locale("en-IN") == "INR"

    def test_de_de_returns_eur(self):
        """de-DE (German) locale should return EUR."""
        assert get_currency_from_browser_locale("de-DE") == "EUR"

    def test_fr_fr_returns_eur(self):
        """fr-FR (French) locale should return EUR."""
        assert get_currency_from_browser_locale("fr-FR") == "EUR"

    def test_it_it_returns_eur(self):
        """it-IT (Italian) locale should return EUR."""
        assert get_currency_from_browser_locale("it-IT") == "EUR"

    def test_es_es_returns_eur(self):
        """es-ES (Spanish) locale should return EUR."""
        assert get_currency_from_browser_locale("es-ES") == "EUR"

    def test_nl_nl_returns_eur(self):
        """nl-NL (Dutch) locale should return EUR."""
        assert get_currency_from_browser_locale("nl-NL") == "EUR"

    def test_pt_pt_returns_eur(self):
        """pt-PT (Portuguese) locale should return EUR."""
        assert get_currency_from_browser_locale("pt-PT") == "EUR"

    def test_de_ch_returns_chf(self):
        """de-CH (Swiss German) locale should return CHF."""
        assert get_currency_from_browser_locale("de-CH") == "CHF"

    def test_fr_ch_returns_chf(self):
        """fr-CH (Swiss French) locale should return CHF."""
        assert get_currency_from_browser_locale("fr-CH") == "CHF"

    def test_it_ch_returns_chf(self):
        """it-CH (Swiss Italian) locale should return CHF."""
        assert get_currency_from_browser_locale("it-CH") == "CHF"

    def test_ja_jp_returns_jpy(self):
        """ja-JP (Japanese) locale should return JPY."""
        assert get_currency_from_browser_locale("ja-JP") == "JPY"

    def test_zh_cn_returns_cny(self):
        """zh-CN (Chinese) locale should return CNY."""
        assert get_currency_from_browser_locale("zh-CN") == "CNY"

    def test_hi_in_returns_inr(self):
        """hi-IN (Hindi) locale should return INR."""
        assert get_currency_from_browser_locale("hi-IN") == "INR"

    def test_pt_br_returns_brl(self):
        """pt-BR (Brazilian Portuguese) locale should return BRL."""
        assert get_currency_from_browser_locale("pt-BR") == "BRL"

    def test_language_fallback_en(self):
        """en (without region) should fall back to USD."""
        assert get_currency_from_browser_locale("en") == "USD"

    def test_language_fallback_de(self):
        """de (without region) should fall back to EUR."""
        assert get_currency_from_browser_locale("de") == "EUR"

    def test_language_fallback_fr(self):
        """fr (without region) should fall back to EUR."""
        assert get_currency_from_browser_locale("fr") == "EUR"

    def test_language_fallback_ja(self):
        """ja (without region) should fall back to JPY."""
        assert get_currency_from_browser_locale("ja") == "JPY"

    def test_language_fallback_zh(self):
        """zh (without region) should fall back to CNY."""
        assert get_currency_from_browser_locale("zh") == "CNY"

    def test_unknown_locale_returns_usd(self):
        """Unknown locale should fall back to USD."""
        assert get_currency_from_browser_locale("xx-XX") == "USD"
        assert get_currency_from_browser_locale("invalid") == "USD"

    def test_case_insensitive_en_us(self):
        """Locale matching should be case-insensitive."""
        assert get_currency_from_browser_locale("EN-US") == "USD"
        assert get_currency_from_browser_locale("En-Us") == "USD"

    def test_case_insensitive_de_de(self):
        """Locale matching should be case-insensitive."""
        assert get_currency_from_browser_locale("DE-DE") == "EUR"
        assert get_currency_from_browser_locale("De-De") == "EUR"
