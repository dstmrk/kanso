"""Data loading utilities for Google Sheets integration."""

import asyncio
import logging

from nicegui import app

from app.services.data_loader_core import DataLoaderCore

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
        from app.core.config import config as app_config

        try:
            # Create core loader with NiceGUI storage
            loader = DataLoaderCore(app.storage.user, app_config)

            # Check if data already loaded
            if loader.all_data_loaded():
                logger.info("All data sheets already loaded")
                return True

            # Get credentials
            credentials = loader.get_credentials()
            if not credentials:
                raise RuntimeError(
                    "Google Sheets not configured. Please complete the onboarding setup."
                )

            creds_dict, url = credentials

            # Create service and load sheets
            service = loader.create_google_sheet_service(creds_dict, url)
            return loader.load_missing_sheets(service)

        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return False

    # Run the blocking I/O operation in a separate thread using asyncio.to_thread
    return await asyncio.to_thread(load_data_sync)
