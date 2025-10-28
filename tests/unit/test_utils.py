"""Tests for utility functions in app/services/utils.py"""

from datetime import UTC, datetime, timedelta

from app.services.utils import (
    format_currency,
    format_percentage,
    format_timestamp_relative,
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

        formatted, relative = format_timestamp_relative(timestamp)
        assert "minute" in relative
        assert "ago" in relative

    def test_single_minute_ago(self):
        """1 minute ago should use singular 'minute'."""
        now = datetime.now(UTC)
        timestamp = (now - timedelta(minutes=1, seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

        formatted, relative = format_timestamp_relative(timestamp)
        assert relative == "1 minute ago"

    def test_multiple_minutes_ago(self):
        """Multiple minutes should use plural 'minutes'."""
        now = datetime.now(UTC)
        timestamp = (now - timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ")

        formatted, relative = format_timestamp_relative(timestamp)
        assert "minutes ago" in relative

    def test_hours_ago(self):
        """Timestamp within a day should show hours."""
        now = datetime.now(UTC)
        timestamp = (now - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")

        formatted, relative = format_timestamp_relative(timestamp)
        assert "hour" in relative
        assert "ago" in relative

    def test_single_hour_ago(self):
        """1 hour ago should use singular 'hour'."""
        now = datetime.now(UTC)
        timestamp = (now - timedelta(hours=1, minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

        formatted, relative = format_timestamp_relative(timestamp)
        assert relative == "1 hour ago"

    def test_days_ago(self):
        """Timestamp within a week should show days."""
        now = datetime.now(UTC)
        timestamp = (now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")

        formatted, relative = format_timestamp_relative(timestamp)
        assert "day" in relative
        assert "ago" in relative

    def test_single_day_ago(self):
        """1 day ago should use singular 'day'."""
        now = datetime.now(UTC)
        timestamp = (now - timedelta(days=1, hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")

        formatted, relative = format_timestamp_relative(timestamp)
        assert relative == "1 day ago"

    def test_weeks_ago(self):
        """Timestamp within a month should show weeks."""
        now = datetime.now(UTC)
        timestamp = (now - timedelta(weeks=2)).strftime("%Y-%m-%dT%H:%M:%SZ")

        formatted, relative = format_timestamp_relative(timestamp)
        assert "week" in relative
        assert "ago" in relative

    def test_months_ago(self):
        """Timestamp over a month should show months."""
        now = datetime.now(UTC)
        timestamp = (now - timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%SZ")

        formatted, relative = format_timestamp_relative(timestamp)
        assert "month" in relative
        assert "ago" in relative

    def test_formatted_absolute_time(self):
        """Should return formatted absolute time in YYYY-MM-DD HH:MM:SS format."""
        timestamp = "2025-10-18T14:30:45Z"
        formatted, relative = format_timestamp_relative(timestamp)

        # Check format
        assert formatted == "2025-10-18 14:30:45"
        assert len(formatted) == 19

    def test_invalid_timestamp_format(self):
        """Invalid timestamp should return 'Invalid timestamp'."""
        formatted, relative = format_timestamp_relative("not-a-timestamp")
        assert formatted == "Invalid timestamp"
        assert relative == ""
