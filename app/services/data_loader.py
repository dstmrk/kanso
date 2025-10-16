"""Data loading utilities for Google Sheets integration."""

import asyncio
import logging

from nicegui import app

logger = logging.getLogger(__name__)


async def ensure_data_loaded():
    """Lazy load data sheets from Google Sheets if not already in storage.

    This function runs the I/O-bound operation in a separate thread to avoid blocking
    the UI. It checks if data is already loaded and only fetches missing sheets.

    Returns:
        bool: True if all data was loaded successfully, False otherwise.
    """

    def load_data_sync():
        """Synchronous data loading function that runs in background thread."""
        import json
        import tempfile
        from pathlib import Path

        from app.core.config import config as app_config
        from app.services.google_sheets import GoogleSheetService

        try:
            # Check if all data is already loaded
            if (
                app.storage.user.get("data_sheet")
                and app.storage.user.get("assets_sheet")
                and app.storage.user.get("liabilities_sheet")
                and app.storage.user.get("expenses_sheet")
            ):
                logger.info("All data sheets already loaded")
                return True

            # Get credentials from user storage
            custom_creds_json = app.storage.user.get("google_credentials_json")
            custom_url = app.storage.user.get("custom_workbook_url")

            if not custom_creds_json or not custom_url:
                raise RuntimeError(
                    "Google Sheets not configured. Please complete the onboarding setup."
                )

            # Initialize Google Sheets service
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=True) as tmp:
                json.dump(json.loads(custom_creds_json), tmp, indent=2)
                tmp.flush()
                tmp_path = Path(tmp.name)
                service = GoogleSheetService(tmp_path, custom_url)

            # Load missing sheets
            if not app.storage.user.get("data_sheet"):
                logger.info("Loading Data sheet...")
                app.storage.user["data_sheet"] = service.get_worksheet_as_dataframe(
                    app_config.data_sheet_name
                ).to_json(orient="split")

            if not app.storage.user.get("assets_sheet"):
                logger.info("Loading Assets sheet...")
                app.storage.user["assets_sheet"] = service.get_worksheet_as_dataframe(
                    app_config.assets_sheet_name, header=[0, 1]
                ).to_json(orient="split")

            if not app.storage.user.get("liabilities_sheet"):
                logger.info("Loading Liabilities sheet...")
                app.storage.user["liabilities_sheet"] = service.get_worksheet_as_dataframe(
                    app_config.liabilities_sheet_name, header=[0, 1]
                ).to_json(orient="split")

            if not app.storage.user.get("expenses_sheet"):
                logger.info("Loading Expenses sheet...")
                app.storage.user["expenses_sheet"] = service.get_worksheet_as_dataframe(
                    app_config.expenses_sheet_name
                ).to_json(orient="split")

            logger.info("All data sheets loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return False

    # Run the blocking I/O operation in a separate thread using asyncio.to_thread
    return await asyncio.to_thread(load_data_sync)
