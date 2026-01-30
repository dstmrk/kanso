"""Data loading utilities for Google Sheets integration."""

import asyncio
import logging
from datetime import UTC

from nicegui import app

from app.core.exceptions import ConfigurationError, ExternalServiceError
from app.services.data_loader_core import DataLoaderCore

logger = logging.getLogger(__name__)

ALL_SHEETS_LABEL: str = "All sheets"


def _is_data_fresh(storage: dict, ttl_seconds: float) -> bool | None:
    """Check if cached data is still within TTL.

    Returns True if fresh, False if stale, None if no timestamp exists.
    """
    from datetime import datetime

    last_refresh = storage.get("last_data_refresh")
    if not last_refresh:
        return None

    try:
        age_seconds = (datetime.now(UTC) - datetime.fromisoformat(last_refresh)).total_seconds()
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid timestamp format: {e}, will reload data")
        return False

    if age_seconds < ttl_seconds:
        logger.info(f"Data is fresh (age: {age_seconds:.0f}s / {ttl_seconds}s TTL)")
        return True

    logger.info(f"Data is stale (age: {age_seconds:.0f}s), will refresh from Google Sheets")
    return False


def _load_from_google_sheets(loader: DataLoaderCore, storage: dict) -> bool:
    """Obtain credentials, create service, and load missing sheets."""
    from app.services.utils import get_current_timestamp

    credentials = loader.get_credentials()
    if not credentials:
        raise ConfigurationError(
            "Google Sheets credentials not configured",
            user_message="Please complete the setup in Settings to connect your Google Sheet.",
        )

    creds_dict, url = credentials
    service = loader.create_google_sheet_service(creds_dict, url)
    success = loader.load_missing_sheets(service)

    if success and "last_data_refresh" not in storage:
        storage["last_data_refresh"] = get_current_timestamp()
        logger.info("First data load timestamp saved")

    return success


async def ensure_data_loaded():
    """Lazy load data sheets from Google Sheets if not already in storage.

    This function runs the I/O-bound operation in a separate thread to avoid blocking
    the UI. It checks if data is already loaded and respects a 24h cache TTL to avoid
    unnecessary reloads. Users can still manually refresh using the refresh button.

    Returns:
        bool: True if all data was loaded successfully, False otherwise.
    """

    def load_data_sync():
        """Synchronous data loading function that runs in background thread."""
        from app.core.config import config as app_config
        from app.core.constants import DATA_REFRESH_TTL_SECONDS
        from app.services.utils import get_current_timestamp

        try:
            loader = DataLoaderCore(app.storage.general, app_config)
            storage = app.storage.general

            if loader.all_data_loaded():
                freshness = _is_data_fresh(storage, DATA_REFRESH_TTL_SECONDS)
                if freshness is True:
                    return True
                if freshness is None:
                    # No timestamp exists — save it for backward compatibility
                    storage["last_data_refresh"] = get_current_timestamp()
                    logger.info("First data load timestamp saved (data already present)")
                    return True
                # freshness is False — data is stale, fall through to reload

            return _load_from_google_sheets(loader, storage)

        except (ConfigurationError, ExternalServiceError):
            raise
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Data processing error: {e}", exc_info=True)
            return False

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
                raise ConfigurationError(
                    "Google Sheets credentials not configured",
                    user_message="Please complete the setup in Settings to connect your Google Sheet.",
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

        except ConfigurationError as e:
            logger.error(f"Configuration error during refresh: {e}")
            return {
                "updated_count": 0,
                "unchanged_count": 0,
                "failed_count": 4,
                "details": [(ALL_SHEETS_LABEL, False, f"Configuration error: {e.user_message}")],
                "error": e.user_message,
            }
        except ExternalServiceError as e:
            logger.error(f"External service error during refresh: {e}")
            return {
                "updated_count": 0,
                "unchanged_count": 0,
                "failed_count": 4,
                "details": [(ALL_SHEETS_LABEL, False, f"Connection error: {e.user_message}")],
                "error": e.user_message,
            }
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Data processing error during refresh: {e}", exc_info=True)
            return {
                "updated_count": 0,
                "unchanged_count": 0,
                "failed_count": 4,
                "details": [(ALL_SHEETS_LABEL, False, f"Data error: {str(e)}")],
                "error": str(e),
            }

    # Run the blocking I/O operation in a separate thread
    return await asyncio.to_thread(refresh_data_sync)
