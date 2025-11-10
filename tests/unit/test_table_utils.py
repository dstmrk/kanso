"""Tests for table utility functions (CSV export, mobile messages, etc.)."""

from unittest.mock import MagicMock

import pandas as pd

from app.ui.table_utils import export_dataframe_to_csv


class TestExportDataframeToCSV:
    """Test CSV export functionality."""

    def test_basic_export(self, monkeypatch):
        """Test basic CSV export with valid DataFrame."""
        # Mock ui.download and ui.notify
        mock_download = MagicMock()
        mock_notify = MagicMock()
        monkeypatch.setattr("app.ui.table_utils.ui.download", mock_download)
        monkeypatch.setattr("app.ui.table_utils.ui.notify", mock_notify)

        # Create test DataFrame
        df = pd.DataFrame(
            {
                "Date": ["2024-01", "2024-02"],
                "Amount": [100.50, 200.75],
                "Category": ["Food", "Transport"],
            }
        )

        # Export
        export_dataframe_to_csv(df, "test_export")

        # Verify download was called
        assert mock_download.call_count == 1
        call_args = mock_download.call_args

        # Verify CSV content
        csv_content = call_args[0][0].decode("utf-8")
        assert "Date,Amount,Category" in csv_content
        assert "2024-01,100.5,Food" in csv_content
        assert "2024-02,200.75,Transport" in csv_content

        # Verify filename format: test_export_YYYYMMDD_HHMMSS.csv
        filename = call_args[0][1]
        assert filename.startswith("test_export_")
        assert filename.endswith(".csv")
        # Filename should be: prefix_YYYYMMDD_HHMMSS.csv
        # Example: test_export_20241106_143022.csv
        assert len(filename.split("_")) >= 3  # Prefix might contain underscores

        # Verify notification
        mock_notify.assert_called_once_with("✓ Exported to CSV", type="positive")

    def test_export_with_columns_to_drop(self, monkeypatch):
        """Test CSV export with column dropping."""
        mock_download = MagicMock()
        mock_notify = MagicMock()
        monkeypatch.setattr("app.ui.table_utils.ui.download", mock_download)
        monkeypatch.setattr("app.ui.table_utils.ui.notify", mock_notify)

        # Create test DataFrame with extra columns
        df = pd.DataFrame(
            {
                "Date": ["2024-01", "2024-02"],
                "Date_DT": ["datetime1", "datetime2"],  # Internal column to drop
                "Amount": [100.50, 200.75],
                "Category": ["Food", "Transport"],
                "Internal_ID": [1, 2],  # Another internal column
            }
        )

        # Export with columns to drop
        export_dataframe_to_csv(df, "test_export", columns_to_drop=["Date_DT", "Internal_ID"])

        # Verify CSV content doesn't include dropped columns
        csv_content = mock_download.call_args[0][0].decode("utf-8")
        assert "Date,Amount,Category" in csv_content
        assert "Date_DT" not in csv_content
        assert "Internal_ID" not in csv_content
        assert "2024-01,100.5,Food" in csv_content

    def test_export_with_nonexistent_columns_to_drop(self, monkeypatch):
        """Test CSV export with non-existent columns in drop list (should not error)."""
        mock_download = MagicMock()
        mock_notify = MagicMock()
        monkeypatch.setattr("app.ui.table_utils.ui.download", mock_download)
        monkeypatch.setattr("app.ui.table_utils.ui.notify", mock_notify)

        df = pd.DataFrame(
            {
                "Date": ["2024-01"],
                "Amount": [100.50],
            }
        )

        # Try to drop columns that don't exist (should handle gracefully)
        export_dataframe_to_csv(df, "test_export", columns_to_drop=["NonExistent", "AlsoNope"])

        # Should still export successfully
        csv_content = mock_download.call_args[0][0].decode("utf-8")
        assert "Date,Amount" in csv_content
        assert "2024-01,100.5" in csv_content

    def test_export_empty_dataframe(self, monkeypatch):
        """Test CSV export with empty DataFrame."""
        mock_download = MagicMock()
        mock_notify = MagicMock()
        monkeypatch.setattr("app.ui.table_utils.ui.download", mock_download)
        monkeypatch.setattr("app.ui.table_utils.ui.notify", mock_notify)

        # Empty DataFrame with columns
        df = pd.DataFrame(columns=["Date", "Amount"])

        export_dataframe_to_csv(df, "test_export")

        # Should export header only
        csv_content = mock_download.call_args[0][0].decode("utf-8")
        assert "Date,Amount" in csv_content
        assert csv_content.strip() == "Date,Amount"
