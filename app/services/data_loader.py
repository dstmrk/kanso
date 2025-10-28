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
        from app.services.utils import get_current_timestamp

        try:
            # Create core loader with general storage (shared across devices)
            loader = DataLoaderCore(app.storage.general, app_config)

            # Check if data already loaded
            if loader.all_data_loaded():
                logger.info("All data sheets already loaded")
                # Save timestamp if this is the first time we check (e.g., after onboarding)
                if "last_data_refresh" not in app.storage.general:
                    app.storage.general["last_data_refresh"] = get_current_timestamp()
                    logger.info("First data load timestamp saved (data already present)")
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
            success = loader.load_missing_sheets(service)

            # Save timestamp of first data load
            if success and "last_data_refresh" not in app.storage.general:
                app.storage.general["last_data_refresh"] = get_current_timestamp()
                logger.info("First data load timestamp saved")

            return success

        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return False

    # Run the blocking I/O operation in a separate thread using asyncio.to_thread
    return await asyncio.to_thread(load_data_sync)


async def refresh_all_data():
    """Force refresh all data sheets from Google Sheets.

    This function:
    1. Loads fresh data from Google Sheets
    2. Compares with existing data using hashes
    3. Updates storage only for changed sheets
    4. Updates the last refresh timestamp
    5. Returns detailed results about what was updated

    Returns:
        dict: Results with updated_count, unchanged_count, failed_count, and details
    """

    def refresh_data_sync():
        """Synchronous data refresh function that runs in background thread."""
        from app.core.config import config as app_config
        from app.services.utils import get_current_timestamp

        try:
            # Create core loader with general storage (shared across devices)
            loader = DataLoaderCore(app.storage.general, app_config)

            # Get credentials
            credentials = loader.get_credentials()
            if not credentials:
                raise RuntimeError(
                    "Google Sheets not configured. Please complete the onboarding setup."
                )

            creds_dict, url = credentials

            # Create service
            service = loader.create_google_sheet_service(creds_dict, url)

            # Refresh all sheets with change detection
            results = loader.refresh_all_sheets(service)

            # Update timestamp if any sheet was updated or this is first refresh
            if results["updated_count"] > 0 or "last_data_refresh" not in app.storage.general:
                app.storage.general["last_data_refresh"] = get_current_timestamp()
                logger.info(f"Data refresh completed: {results['updated_count']} updated")

            return results

        except Exception as e:
            logger.error(f"Failed to refresh data: {e}")
            return {
                "updated_count": 0,
                "unchanged_count": 0,
                "failed_count": 4,  # All sheets failed (Assets, Liabilities, Expenses, Incomes)
                "details": [("All sheets", False, f"Error: {str(e)}")],
                "error": str(e),
            }

    # Run the blocking I/O operation in a separate thread
    return await asyncio.to_thread(refresh_data_sync)
