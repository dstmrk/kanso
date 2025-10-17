"""Unit tests for DataLoaderCore (framework-independent business logic)."""

import json
from unittest.mock import MagicMock, patch

from app.services.data_loader_core import DataLoaderCore


class MockStorage:
    """Mock storage for testing."""

    def __init__(self, initial_data=None):
        self.data = initial_data or {}

    def get(self, key):
        return self.data.get(key)

    def __setitem__(self, key, value):
        self.data[key] = value


class MockConfig:
    """Mock configuration for testing."""

    def __init__(self):
        self.data_sheet_name = "Data"
        self.assets_sheet_name = "Assets"
        self.liabilities_sheet_name = "Liabilities"
        self.expenses_sheet_name = "Expenses"


class TestDataLoaderCore:
    """Tests for DataLoaderCore business logic."""

    def test_all_data_loaded_returns_true_when_all_sheets_present(self):
        """Test that all_data_loaded returns True when all sheets are in storage."""
        storage = MockStorage(
            {
                "data_sheet": "mock_data",
                "assets_sheet": "mock_assets",
                "liabilities_sheet": "mock_liabilities",
                "expenses_sheet": "mock_expenses",
            }
        )
        config = MockConfig()
        loader = DataLoaderCore(storage, config)

        assert loader.all_data_loaded() is True

    def test_all_data_loaded_returns_false_when_missing_sheets(self):
        """Test that all_data_loaded returns False when any sheet is missing."""
        storage = MockStorage(
            {
                "data_sheet": "mock_data",
                "assets_sheet": "mock_assets",
                # Missing liabilities and expenses
            }
        )
        config = MockConfig()
        loader = DataLoaderCore(storage, config)

        assert loader.all_data_loaded() is False

    def test_all_data_loaded_returns_false_when_storage_empty(self):
        """Test that all_data_loaded returns False when storage is empty."""
        storage = MockStorage()
        config = MockConfig()
        loader = DataLoaderCore(storage, config)

        assert loader.all_data_loaded() is False

    def test_get_credentials_returns_tuple_when_valid(self):
        """Test that get_credentials returns credentials and URL when valid."""
        credentials = {"type": "service_account", "project_id": "test"}
        storage = MockStorage(
            {
                "google_credentials_json": json.dumps(credentials),
                "custom_workbook_url": "https://docs.google.com/spreadsheets/d/test",
            }
        )
        config = MockConfig()
        loader = DataLoaderCore(storage, config)

        result = loader.get_credentials()

        assert result is not None
        creds_dict, url = result
        assert creds_dict == credentials
        assert url == "https://docs.google.com/spreadsheets/d/test"

    def test_get_credentials_returns_none_when_missing_creds(self):
        """Test that get_credentials returns None when credentials are missing."""
        storage = MockStorage({"custom_workbook_url": "https://example.com"})
        config = MockConfig()
        loader = DataLoaderCore(storage, config)

        result = loader.get_credentials()

        assert result is None

    def test_get_credentials_returns_none_when_missing_url(self):
        """Test that get_credentials returns None when URL is missing."""
        credentials = {"type": "service_account"}
        storage = MockStorage({"google_credentials_json": json.dumps(credentials)})
        config = MockConfig()
        loader = DataLoaderCore(storage, config)

        result = loader.get_credentials()

        assert result is None

    def test_get_credentials_returns_none_when_invalid_json(self):
        """Test that get_credentials returns None when JSON is invalid."""
        storage = MockStorage(
            {
                "google_credentials_json": "invalid json {",
                "custom_workbook_url": "https://example.com",
            }
        )
        config = MockConfig()
        loader = DataLoaderCore(storage, config)

        result = loader.get_credentials()

        assert result is None

    def test_load_missing_sheets_loads_all_when_none_exist(self):
        """Test that load_missing_sheets loads all sheets when none exist."""
        storage = MockStorage()
        config = MockConfig()
        loader = DataLoaderCore(storage, config)

        # Mock service
        mock_service = MagicMock()
        mock_df = MagicMock()
        mock_df.to_json.return_value = '{"data": "mocked"}'
        mock_service.get_worksheet_as_dataframe.return_value = mock_df

        result = loader.load_missing_sheets(mock_service)

        assert result is True
        assert "data_sheet" in storage.data
        assert "assets_sheet" in storage.data
        assert "liabilities_sheet" in storage.data
        assert "expenses_sheet" in storage.data
        # Should have called for all 4 sheets
        assert mock_service.get_worksheet_as_dataframe.call_count == 4

    def test_load_missing_sheets_loads_only_missing(self):
        """Test that load_missing_sheets loads only missing sheets."""
        storage = MockStorage(
            {
                "data_sheet": "existing_data",
                "assets_sheet": "existing_assets",
                # Missing liabilities and expenses
            }
        )
        config = MockConfig()
        loader = DataLoaderCore(storage, config)

        # Mock service
        mock_service = MagicMock()
        mock_df = MagicMock()
        mock_df.to_json.return_value = '{"data": "mocked"}'
        mock_service.get_worksheet_as_dataframe.return_value = mock_df

        result = loader.load_missing_sheets(mock_service)

        assert result is True
        assert "liabilities_sheet" in storage.data
        assert "expenses_sheet" in storage.data
        # Should have called for only 2 missing sheets
        assert mock_service.get_worksheet_as_dataframe.call_count == 2

    def test_load_missing_sheets_returns_false_on_error(self):
        """Test that load_missing_sheets returns False when an error occurs."""
        storage = MockStorage()
        config = MockConfig()
        loader = DataLoaderCore(storage, config)

        # Mock service that raises exception
        mock_service = MagicMock()
        mock_service.get_worksheet_as_dataframe.side_effect = Exception("Connection failed")

        result = loader.load_missing_sheets(mock_service)

        assert result is False

    def test_create_google_sheet_service_with_valid_credentials(self):
        """Test creating GoogleSheetService with valid credentials."""
        storage = MockStorage()
        config = MockConfig()
        loader = DataLoaderCore(storage, config)

        credentials = {"type": "service_account", "project_id": "test", "private_key": "fake"}
        url = "https://docs.google.com/spreadsheets/d/test"

        # Patch where it's imported, not where it's defined
        with patch("app.services.google_sheets.GoogleSheetService") as mock_service_class:
            mock_service_instance = MagicMock()
            mock_service_class.return_value = mock_service_instance

            service = loader.create_google_sheet_service(credentials, url)

            assert service == mock_service_instance
            mock_service_class.assert_called_once()
            # Verify it was called with a Path and the URL
            call_args = mock_service_class.call_args
            assert str(call_args[0][1]) == url

    def test_load_missing_sheets_uses_correct_sheet_names_from_config(self):
        """Test that load_missing_sheets uses sheet names from config."""
        storage = MockStorage()
        config = MockConfig()
        config.data_sheet_name = "CustomData"
        config.assets_sheet_name = "CustomAssets"
        config.liabilities_sheet_name = "CustomLiabilities"
        config.expenses_sheet_name = "CustomExpenses"
        loader = DataLoaderCore(storage, config)

        mock_service = MagicMock()
        mock_df = MagicMock()
        mock_df.to_json.return_value = '{"data": "mocked"}'
        mock_service.get_worksheet_as_dataframe.return_value = mock_df

        loader.load_missing_sheets(mock_service)

        # Verify correct sheet names were used
        calls = mock_service.get_worksheet_as_dataframe.call_args_list
        assert any("CustomData" in str(call) for call in calls)
        assert any("CustomAssets" in str(call) for call in calls)
        assert any("CustomLiabilities" in str(call) for call in calls)
        assert any("CustomExpenses" in str(call) for call in calls)
