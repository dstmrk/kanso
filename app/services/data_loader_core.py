"""Core data loading logic separated from NiceGUI for testability."""

import hashlib
import json
import logging
from typing import Any, Protocol

import pandas as pd

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
            self.storage.get("assets_sheet")
            and self.storage.get("liabilities_sheet")
            and self.storage.get("expenses_sheet")
            and self.storage.get("incomes_sheet")
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
            sheets_loaded = []

            if not self.storage.get("assets_sheet"):
                logger.debug("Loading Assets sheet...")
                df = service.get_worksheet_as_dataframe(
                    self.app_config.assets_sheet_name, header=[0, 1]
                )
                self.storage["assets_sheet"] = df.to_json(orient="split")
                self.storage["assets_sheet_hash"] = self.calculate_dataframe_hash(df)
                sheets_loaded.append(f"Assets ({len(df)} rows)")

            if not self.storage.get("liabilities_sheet"):
                logger.debug("Loading Liabilities sheet...")
                df = service.get_worksheet_as_dataframe(
                    self.app_config.liabilities_sheet_name, header=[0, 1]
                )
                self.storage["liabilities_sheet"] = df.to_json(orient="split")
                self.storage["liabilities_sheet_hash"] = self.calculate_dataframe_hash(df)
                sheets_loaded.append(f"Liabilities ({len(df)} rows)")

            if not self.storage.get("expenses_sheet"):
                logger.debug("Loading Expenses sheet...")
                df = service.get_worksheet_as_dataframe(self.app_config.expenses_sheet_name)
                self.storage["expenses_sheet"] = df.to_json(orient="split")
                self.storage["expenses_sheet_hash"] = self.calculate_dataframe_hash(df)
                sheets_loaded.append(f"Expenses ({len(df)} rows)")

            if not self.storage.get("incomes_sheet"):
                logger.debug("Loading Incomes sheet...")
                # Load with multi-index header like Assets/Liabilities
                df = service.get_worksheet_as_dataframe(
                    self.app_config.incomes_sheet_name, header=[0, 1]
                )
                logger.debug(
                    f"Incomes sheet loaded with {len(df)} rows and columns: {df.columns.tolist()[:5]}"
                )
                self.storage["incomes_sheet"] = df.to_json(orient="split")
                self.storage["incomes_sheet_hash"] = self.calculate_dataframe_hash(df)
                sheets_loaded.append(f"Incomes ({len(df)} rows)")

            if sheets_loaded:
                logger.info(f"Data sheets loaded successfully: {', '.join(sheets_loaded)}")
            else:
                logger.debug("All data sheets already loaded (skipped)")
            return True

        except Exception as e:
            logger.error(f"Failed to load sheets: {e}")
            return False

    def create_google_sheet_service(self, credentials_dict: dict, url: str):
        """Create GoogleSheetService with credentials dict.

        Args:
            credentials_dict: Credentials as dictionary
            url: Google Sheets URL

        Returns:
            GoogleSheetService instance
        """
        from app.services.google_sheets import GoogleSheetService

        # Pass credentials dict directly - no temp file needed
        return GoogleSheetService(credentials_dict, url)

    @staticmethod
    def calculate_dataframe_hash(df: pd.DataFrame) -> str:
        """Calculate MD5 hash of a DataFrame for change detection.

        Args:
            df: DataFrame to hash

        Returns:
            MD5 hash string of the DataFrame content
        """
        # Convert DataFrame to JSON string for consistent hashing
        df_json = df.to_json(orient="split", date_format="iso")
        return hashlib.md5(df_json.encode()).hexdigest()

    def refresh_sheet(
        self, service, sheet_name: str, storage_key: str, header: list[int] | int = 0
    ) -> tuple[bool, str]:
        """Force refresh a single sheet from Google Sheets.

        Loads fresh data from Google Sheets, calculates hash, and updates storage
        only if data has changed.

        Args:
            service: GoogleSheetService instance
            sheet_name: Name of the worksheet to refresh
            storage_key: Key in storage (e.g., 'assets_sheet')
            header: Header row(s) - 0 for single header, [0, 1] for multi-index (default: 0)

        Returns:
            Tuple of (changed: bool, message: str) indicating if data was updated
        """
        try:
            # Load fresh data from Google Sheets
            logger.debug(f"Refreshing {sheet_name} sheet from Google Sheets...")
            df = service.get_worksheet_as_dataframe(sheet_name, header=header)

            # Calculate hash of new data
            new_hash = self.calculate_dataframe_hash(df)
            hash_key = f"{storage_key}_hash"

            # Get existing hash
            existing_hash = self.storage.get(hash_key)

            # Compare hashes
            if existing_hash == new_hash:
                logger.debug(f"No changes detected in {sheet_name} sheet")
                return False, f"No changes in {sheet_name}"

            # Data has changed - update storage
            self.storage[storage_key] = df.to_json(orient="split")
            self.storage[hash_key] = new_hash
            logger.info(f"Updated {sheet_name} sheet - data changed ({len(df)} rows)")

            return True, f"Updated {sheet_name}"

        except Exception as e:
            error_msg = f"Failed to refresh {sheet_name}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def refresh_all_sheets(self, service) -> dict[str, Any]:
        """Refresh all sheets from Google Sheets with change detection.

        Args:
            service: GoogleSheetService instance

        Returns:
            Dictionary with refresh results:
                - updated_count: Number of sheets that changed
                - unchanged_count: Number of sheets unchanged
                - failed_count: Number of sheets that failed
                - details: List of (sheet_name, changed, message) tuples
        """
        sheets_to_refresh = [
            (self.app_config.assets_sheet_name, "assets_sheet", [0, 1]),
            (self.app_config.liabilities_sheet_name, "liabilities_sheet", [0, 1]),
            (self.app_config.expenses_sheet_name, "expenses_sheet", 0),
            (self.app_config.incomes_sheet_name, "incomes_sheet", [0, 1]),
        ]

        results: dict[str, Any] = {
            "updated_count": 0,
            "unchanged_count": 0,
            "failed_count": 0,
            "details": [],
        }

        for sheet_name, storage_key, header in sheets_to_refresh:
            # Type cast header to satisfy mypy (it's always int or list[int] from our tuple)
            header_typed: int | list[int] = header  # type: ignore[assignment]
            changed, message = self.refresh_sheet(service, sheet_name, storage_key, header_typed)

            if "Failed" in message:
                results["failed_count"] += 1
            elif changed:
                results["updated_count"] += 1
            else:
                results["unchanged_count"] += 1

            results["details"].append((sheet_name, changed, message))

        return results
