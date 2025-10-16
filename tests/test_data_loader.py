"""Tests for the data_loader module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.data_loader import ensure_data_loaded


class TestEnsureDataLoaded:
    """Tests for ensure_data_loaded function."""

    @pytest.mark.asyncio
    async def test_data_already_loaded_returns_true(self):
        """Test that function returns True when all data is already loaded."""
        mock_storage_user = MagicMock()
        mock_storage_user.get.side_effect = lambda k: {
            "data_sheet": "mock_data",
            "assets_sheet": "mock_assets",
            "liabilities_sheet": "mock_liabilities",
            "expenses_sheet": "mock_expenses",
        }.get(k)

        with patch("app.services.data_loader.app") as mock_app:
            mock_app.storage.user = mock_storage_user
            result = await ensure_data_loaded()

        assert result is True

    @pytest.mark.asyncio
    async def test_load_all_sheets_when_none_exist(self):
        """Test loading all sheets when none are in storage."""
        mock_storage = {}
        mock_service = MagicMock()
        mock_df = MagicMock()
        mock_df.to_json.return_value = '{"data": "mocked"}'
        mock_service.get_worksheet_as_dataframe.return_value = mock_df

        credentials_json = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key": "fake-key",
        }

        def storage_get(key):
            if key == "google_credentials_json":
                return json.dumps(credentials_json)
            elif key == "custom_workbook_url":
                return "https://docs.google.com/spreadsheets/d/test"
            return mock_storage.get(key)

        def storage_set(key, value):
            mock_storage[key] = value

        with (
            patch("app.services.data_loader.app.storage.user.get", side_effect=storage_get),
            patch("app.services.data_loader.app.storage.user.__setitem__", side_effect=storage_set),
            patch("app.services.data_loader.GoogleSheetService", return_value=mock_service),
        ):
            result = await ensure_data_loaded()

        assert result is True
        assert "data_sheet" in mock_storage
        assert "assets_sheet" in mock_storage
        assert "liabilities_sheet" in mock_storage
        assert "expenses_sheet" in mock_storage

    @pytest.mark.asyncio
    async def test_load_only_missing_sheets(self):
        """Test that only missing sheets are loaded."""
        mock_storage = {
            "data_sheet": "existing_data",
            "assets_sheet": "existing_assets",
            # liabilities and expenses are missing
        }
        mock_service = MagicMock()
        mock_df = MagicMock()
        mock_df.to_json.return_value = '{"data": "mocked"}'
        mock_service.get_worksheet_as_dataframe.return_value = mock_df

        credentials_json = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key": "fake-key",
        }

        def storage_get(key):
            if key == "google_credentials_json":
                return json.dumps(credentials_json)
            elif key == "custom_workbook_url":
                return "https://docs.google.com/spreadsheets/d/test"
            return mock_storage.get(key)

        def storage_set(key, value):
            mock_storage[key] = value

        with (
            patch("app.services.data_loader.app.storage.user.get", side_effect=storage_get),
            patch("app.services.data_loader.app.storage.user.__setitem__", side_effect=storage_set),
            patch("app.services.data_loader.GoogleSheetService", return_value=mock_service),
        ):
            result = await ensure_data_loaded()

        assert result is True
        # Should have loaded the missing sheets
        assert "liabilities_sheet" in mock_storage
        assert "expenses_sheet" in mock_storage
        # Shouldn't have called for sheets that already existed
        assert mock_service.get_worksheet_as_dataframe.call_count == 2

    @pytest.mark.asyncio
    async def test_returns_false_on_error(self):
        """Test that function returns False when an error occurs."""
        mock_storage = {}

        def storage_get(key):
            if key == "google_credentials_json":
                return json.dumps({"type": "service_account"})
            elif key == "custom_workbook_url":
                return "https://docs.google.com/spreadsheets/d/test"
            return mock_storage.get(key)

        # Mock GoogleSheetService to raise an exception
        with (
            patch("app.services.data_loader.app.storage.user.get", side_effect=storage_get),
            patch(
                "app.services.data_loader.GoogleSheetService",
                side_effect=Exception("Connection failed"),
            ),
        ):
            result = await ensure_data_loaded()

        assert result is False

    @pytest.mark.asyncio
    async def test_missing_credentials_raises_error(self):
        """Test that missing credentials raises RuntimeError."""
        with patch("app.services.data_loader.app.storage.user.get", return_value=None):
            result = await ensure_data_loaded()

        assert result is False

    @pytest.mark.asyncio
    async def test_invalid_json_credentials_returns_false(self):
        """Test that invalid JSON credentials returns False."""

        def storage_get(key):
            if key == "google_credentials_json":
                return "invalid json {"
            elif key == "custom_workbook_url":
                return "https://docs.google.com/spreadsheets/d/test"
            return None

        with patch("app.services.data_loader.app.storage.user.get", side_effect=storage_get):
            result = await ensure_data_loaded()

        assert result is False
