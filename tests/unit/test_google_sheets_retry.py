"""Tests for Google Sheets service retry logic."""

from unittest.mock import MagicMock, patch

import gspread
import pytest

from app.services.google_sheets import GoogleSheetService


def create_api_error(code: int = 500, message: str = "Internal error"):
    """Create a mock APIError for testing."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"error": {"code": code, "message": message}}
    return gspread.exceptions.APIError(mock_response)


class TestGoogleSheetsRetryLogic:
    """Tests for retry behavior on transient failures."""

    @pytest.fixture
    def mock_service(self):
        """Create a GoogleSheetService with mocked authentication."""
        with patch.object(GoogleSheetService, "_authenticate") as mock_auth:
            mock_auth.return_value = MagicMock(spec=gspread.Client)
            with patch("pathlib.Path.exists", return_value=True):
                service = GoogleSheetService("fake_creds.json", "https://sheets.google.com/d/123")
                yield service

    def test_fetch_retries_on_api_error(self, mock_service):
        """Should retry fetch on APIError and succeed on third attempt."""
        mock_sheet = MagicMock()
        mock_sheet.get_all_values.side_effect = [
            create_api_error(500, "Internal error"),
            create_api_error(500, "Internal error"),
            [["header"], ["data"]],  # Success on third attempt
        ]
        mock_service.client.open_by_url.return_value.worksheet.return_value = mock_sheet

        result = mock_service._fetch_worksheet_data("TestSheet")

        assert result == [["header"], ["data"]]
        assert mock_sheet.get_all_values.call_count == 3

    def test_fetch_fails_after_max_retries(self, mock_service):
        """Should raise APIError after exhausting all retries."""
        mock_sheet = MagicMock()
        mock_sheet.get_all_values.side_effect = create_api_error(500, "Internal error")
        mock_service.client.open_by_url.return_value.worksheet.return_value = mock_sheet

        with pytest.raises(gspread.exceptions.APIError):
            mock_service._fetch_worksheet_data("TestSheet")

        assert mock_sheet.get_all_values.call_count == 3

    def test_append_retries_on_connection_error(self, mock_service):
        """Should retry append on ConnectionError and succeed."""
        mock_sheet = MagicMock()
        mock_sheet.append_row.side_effect = [
            ConnectionError("Network unreachable"),
            ConnectionError("Network unreachable"),
            {"updates": {"updatedRows": 1}},  # Success on third attempt
        ]
        mock_service.client.open_by_url.return_value.worksheet.return_value = mock_sheet

        result = mock_service._append_row_with_retry("Expenses", ["2024-01-01", "Test", "100"])

        assert result == {"updates": {"updatedRows": 1}}
        assert mock_sheet.append_row.call_count == 3

    def test_no_retry_on_worksheet_not_found(self, mock_service):
        """Should not retry on WorksheetNotFound (not a transient error)."""
        mock_service.client.open_by_url.return_value.worksheet.side_effect = (
            gspread.exceptions.WorksheetNotFound("Sheet not found")
        )

        with pytest.raises(gspread.exceptions.WorksheetNotFound):
            mock_service._fetch_worksheet_data("NonExistentSheet")

        # Should only try once since WorksheetNotFound is not in retry list
        assert mock_service.client.open_by_url.return_value.worksheet.call_count == 1

    def test_fetch_succeeds_on_first_try(self, mock_service):
        """Should return data immediately when no errors occur."""
        mock_sheet = MagicMock()
        mock_sheet.get_all_values.return_value = [["col1", "col2"], ["val1", "val2"]]
        mock_service.client.open_by_url.return_value.worksheet.return_value = mock_sheet

        result = mock_service._fetch_worksheet_data("TestSheet")

        assert result == [["col1", "col2"], ["val1", "val2"]]
        assert mock_sheet.get_all_values.call_count == 1
