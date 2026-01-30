"""Tests for data_loader helper functions."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.services.data_loader import _is_data_fresh, _load_from_google_sheets


class TestIsDataFresh:
    """Tests for _is_data_fresh TTL checker."""

    def test_fresh_data(self):
        """Data within TTL should return True."""
        recent = (datetime.now(UTC) - timedelta(seconds=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        storage = {"last_data_refresh": recent}
        assert _is_data_fresh(storage, 86400) is True

    def test_stale_data(self):
        """Data beyond TTL should return False."""
        old = (datetime.now(UTC) - timedelta(hours=25)).strftime("%Y-%m-%dT%H:%M:%SZ")
        storage = {"last_data_refresh": old}
        assert _is_data_fresh(storage, 86400) is False

    def test_no_timestamp(self):
        """No timestamp should return None."""
        assert _is_data_fresh({}, 86400) is None

    def test_empty_timestamp(self):
        """Empty string timestamp should return None."""
        assert _is_data_fresh({"last_data_refresh": ""}, 86400) is None

    def test_invalid_timestamp_format(self):
        """Invalid timestamp format should return False."""
        storage = {"last_data_refresh": "not-a-date"}
        assert _is_data_fresh(storage, 86400) is False

    def test_exactly_at_ttl_boundary(self):
        """Data exactly at TTL boundary should return False (not fresh)."""
        boundary = (datetime.now(UTC) - timedelta(seconds=86400)).strftime("%Y-%m-%dT%H:%M:%SZ")
        storage = {"last_data_refresh": boundary}
        # At exactly TTL, age_seconds >= TTL, so not fresh
        assert _is_data_fresh(storage, 86400) is False


class TestLoadFromGoogleSheets:
    """Tests for _load_from_google_sheets helper."""

    def test_no_credentials_raises_error(self):
        """Should raise ConfigurationError when no credentials available."""
        from app.core.exceptions import ConfigurationError

        loader = MagicMock()
        loader.get_credentials.return_value = None

        with pytest.raises(ConfigurationError):
            _load_from_google_sheets(loader, {})

    def test_successful_load(self):
        """Should return True and save timestamp on first successful load."""
        loader = MagicMock()
        loader.get_credentials.return_value = ({"key": "value"}, "url")
        loader.load_missing_sheets.return_value = True

        storage: dict = {}
        result = _load_from_google_sheets(loader, storage)
        assert result is True
        assert "last_data_refresh" in storage

    def test_successful_load_existing_timestamp(self):
        """Should not overwrite existing timestamp."""
        loader = MagicMock()
        loader.get_credentials.return_value = ({"key": "value"}, "url")
        loader.load_missing_sheets.return_value = True

        storage = {"last_data_refresh": "existing"}
        _load_from_google_sheets(loader, storage)
        assert storage["last_data_refresh"] == "existing"

    def test_failed_load(self):
        """Should return False and not save timestamp on failure."""
        loader = MagicMock()
        loader.get_credentials.return_value = ({"key": "value"}, "url")
        loader.load_missing_sheets.return_value = False

        storage: dict = {}
        result = _load_from_google_sheets(loader, storage)
        assert result is False
        assert "last_data_refresh" not in storage
