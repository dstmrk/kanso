"""Core data loading logic separated from NiceGUI for testability."""

import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class StorageProtocol(Protocol):
    """Protocol for storage interface to enable dependency injection."""

    def get(self, key: str) -> Any:
        """Get value from storage."""
        ...

    def __setitem__(self, key: str, value: Any) -> None:
        """Set value in storage."""
        ...


class DataLoaderCore:
    """Core data loading logic independent of NiceGUI.

    This class contains the business logic for loading data from Google Sheets,
    separated from the NiceGUI framework for better testability.
    """

    def __init__(self, storage: StorageProtocol, app_config):
        """Initialize with storage dependency.

        Args:
            storage: Storage interface (can be mocked in tests)
            app_config: Application configuration object
        """
        self.storage = storage
        self.app_config = app_config

    def all_data_loaded(self) -> bool:
        """Check if all required data sheets are already loaded."""
        return bool(
            self.storage.get("data_sheet")
            and self.storage.get("assets_sheet")
            and self.storage.get("liabilities_sheet")
            and self.storage.get("expenses_sheet")
        )

    def get_credentials(self) -> tuple[dict, str] | None:
        """Get credentials and URL from storage.

        Returns:
            Tuple of (credentials_dict, workbook_url) or None if not available
        """
        creds_json = self.storage.get("google_credentials_json")
        url = self.storage.get("custom_workbook_url")

        if not creds_json or not url:
            return None

        try:
            creds_dict = json.loads(creds_json)
            return (creds_dict, url)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid credentials JSON: {e}")
            return None

    def load_missing_sheets(self, service) -> bool:
        """Load any missing sheets from Google Sheets.

        Args:
            service: GoogleSheetService instance

        Returns:
            True if all sheets loaded successfully, False otherwise
        """
        try:
            if not self.storage.get("data_sheet"):
                logger.info("Loading Data sheet...")
                df = service.get_worksheet_as_dataframe(self.app_config.data_sheet_name)
                self.storage["data_sheet"] = df.to_json(orient="split")

            if not self.storage.get("assets_sheet"):
                logger.info("Loading Assets sheet...")
                df = service.get_worksheet_as_dataframe(
                    self.app_config.assets_sheet_name, header=[0, 1]
                )
                self.storage["assets_sheet"] = df.to_json(orient="split")

            if not self.storage.get("liabilities_sheet"):
                logger.info("Loading Liabilities sheet...")
                df = service.get_worksheet_as_dataframe(
                    self.app_config.liabilities_sheet_name, header=[0, 1]
                )
                self.storage["liabilities_sheet"] = df.to_json(orient="split")

            if not self.storage.get("expenses_sheet"):
                logger.info("Loading Expenses sheet...")
                df = service.get_worksheet_as_dataframe(self.app_config.expenses_sheet_name)
                self.storage["expenses_sheet"] = df.to_json(orient="split")

            logger.info("All data sheets loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load sheets: {e}")
            return False

    def create_google_sheet_service(self, credentials_dict: dict, url: str):
        """Create GoogleSheetService with temporary credentials file.

        Args:
            credentials_dict: Credentials as dictionary
            url: Google Sheets URL

        Returns:
            GoogleSheetService instance
        """
        from app.services.google_sheets import GoogleSheetService

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=True) as tmp:
            json.dump(credentials_dict, tmp, indent=2)
            tmp.flush()
            return GoogleSheetService(Path(tmp.name), url)
