"""Application configuration management.

This module provides centralized configuration loading from environment variables
with sensible defaults. Configuration includes paths, Google Sheets settings,
app settings, and cache configuration.

Example:
    >>> from app.core.config import AppConfig
    >>> config = AppConfig.from_env(Path(__file__).parent.parent)
    >>> config.validate()
    >>> print(f"Running on port {config.app_port}")
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from app.core.constants import (
    CACHE_TTL_SECONDS,
    SHEET_NAME_ASSETS,
    SHEET_NAME_DATA,
    SHEET_NAME_EXPENSES,
    SHEET_NAME_LIABILITIES,
)

logger = logging.getLogger(__name__)


def _parse_bool(value: str | None, default: bool = False) -> bool:
    """Parse boolean value from environment variable string.

    Args:
        value: String value from environment variable
        default: Default value if None

    Returns:
        Boolean value

    Example:
        >>> _parse_bool("true")
        True
        >>> _parse_bool("false")
        False
        >>> _parse_bool(None, True)
        True
    """
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


@dataclass
class AppConfig:
    """Centralized application configuration.

    Loads configuration from environment variables with defaults. Provides
    properties for computed paths and validation methods.

    Attributes:
        app_root: Root directory of the application
        environment: Current environment (dev/prod)
        debug: Enable debug mode (default: False)
        log_level: Logging level (default: "INFO")
        credentials_folder: Relative path to credentials folder (default: "config/credentials")
        static_files_folder: Relative path to static files (default: "static")
        google_sheet_credentials_filename: Name of credentials JSON file
        workbook_url: URL of Google Sheets workbook
        data_sheet_name: Name of main data worksheet (default: "Data")
        assets_sheet_name: Name of assets worksheet (default: "Assets")
        liabilities_sheet_name: Name of liabilities worksheet (default: "Liabilities")
        expenses_sheet_name: Name of expenses worksheet (default: "Expenses")
        app_port: Port to run the application on (default: 6789)
        root_path: Root path for the application (default: "")
        title: Application title (default: "kanso - your minimal money tracker")
        default_theme: UI theme (default: "light")
        reload: Enable hot-reload for development (default: False)
        uvicorn_log_level: Uvicorn logging level (default: "warning")
        storage_secret: Secret for session storage
        cache_ttl_seconds: Cache TTL in seconds (default: 86400 = 24 hours)

    Example:
        >>> config = AppConfig.from_env(Path.cwd())
        >>> config.validate()
        >>> service = GoogleSheetService(config.credentials_path, config.workbook_url)
    """

    # File paths
    app_root: Path
    credentials_folder: str = "config/credentials"
    static_files_folder: str = "static"

    # Environment settings
    environment: str = "prod"
    debug: bool = False
    log_level: str = "INFO"

    # Google Sheets
    google_sheet_credentials_filename: str | None = None
    workbook_url: str | None = None
    data_sheet_name: str = SHEET_NAME_DATA
    assets_sheet_name: str = SHEET_NAME_ASSETS
    liabilities_sheet_name: str = SHEET_NAME_LIABILITIES
    expenses_sheet_name: str = SHEET_NAME_EXPENSES

    # App settings
    app_port: int = 6789
    root_path: str = ""
    title: str = "kanso - your minimal money tracker"
    default_theme: str = "light"
    reload: bool = False
    uvicorn_log_level: str = "warning"
    storage_secret: str | None = None

    # Cache settings (for data that updates monthly)
    cache_ttl_seconds: int = CACHE_TTL_SECONDS

    @classmethod
    def from_env(cls, app_root: Path) -> "AppConfig":
        """Create configuration from environment variables.

        Loads all configuration from environment variables with sensible defaults.
        Environment variables should be defined in a .env file or system environment.

        Args:
            app_root: Root directory path of the application

        Returns:
            AppConfig instance with values from environment or defaults

        Environment Variables:
            APP_ENV: Environment (dev/prod, default: "prod")
            DEBUG: Enable debug mode (true/false, default: false)
            LOG_LEVEL: Logging level (DEBUG/INFO/WARNING/ERROR, default: "INFO")
            CREDENTIALS_FOLDER: Path to credentials folder (default: "config/credentials")
            STATIC_FILES_FOLDER: Path to static files (default: "static")
            GOOGLE_SHEET_CREDENTIALS_FILENAME: Required - credentials JSON filename
            WORKBOOK_URL: Required - Google Sheets workbook URL
            DATA_SHEET_NAME: Main data worksheet name (default: "Data")
            ASSETS_SHEET_NAME: Assets worksheet name (default: "Assets")
            LIABILITIES_SHEET_NAME: Liabilities worksheet name (default: "Liabilities")
            EXPENSES_SHEET_NAME: Expenses worksheet name (default: "Expenses")
            APP_PORT: Application port (default: 6789)
            ROOT_PATH: Root path (default: "")
            APP_TITLE: Application title
            DEFAULT_THEME: UI theme (default: "light")
            RELOAD: Enable hot-reload (true/false, default: false)
            UVICORN_LOG_LEVEL: Uvicorn logging level (default: "warning")
            CACHE_TTL_SECONDS: Cache TTL in seconds (default: 86400)

        Example:
            >>> # With .env file containing required variables
            >>> config = AppConfig.from_env(Path(__file__).parent)
            >>> print(config.app_port)
            6789
        """
        config = cls(
            app_root=app_root,
            environment=os.getenv("APP_ENV", "prod"),
            debug=_parse_bool(os.getenv("DEBUG"), False),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            credentials_folder=os.getenv("CREDENTIALS_FOLDER", "config/credentials"),
            static_files_folder=os.getenv("STATIC_FILES_FOLDER", "static"),
            google_sheet_credentials_filename=os.getenv("GOOGLE_SHEET_CREDENTIALS_FILENAME"),
            workbook_url=os.getenv("WORKBOOK_URL"),
            data_sheet_name=os.getenv("DATA_SHEET_NAME", SHEET_NAME_DATA),
            assets_sheet_name=os.getenv("ASSETS_SHEET_NAME", SHEET_NAME_ASSETS),
            liabilities_sheet_name=os.getenv("LIABILITIES_SHEET_NAME", SHEET_NAME_LIABILITIES),
            expenses_sheet_name=os.getenv("EXPENSES_SHEET_NAME", SHEET_NAME_EXPENSES),
            app_port=int(os.getenv("APP_PORT", "6789")),
            root_path=os.getenv("ROOT_PATH", ""),
            title=os.getenv("APP_TITLE", "kanso - your minimal money tracker"),
            default_theme=os.getenv("DEFAULT_THEME", "light"),
            reload=_parse_bool(os.getenv("RELOAD"), False),
            uvicorn_log_level=os.getenv("UVICORN_LOG_LEVEL", "warning"),
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", str(CACHE_TTL_SECONDS))),
        )
        logger.info(
            f"Configuration loaded: env={config.environment}, debug={config.debug}, "
            f"port={config.app_port}, reload={config.reload}, cache_ttl={config.cache_ttl_seconds}s"
        )
        return config

    @property
    def credentials_path(self) -> Path:
        """Get full absolute path to credentials file.

        Returns:
            Path object pointing to the credentials JSON file

        Raises:
            ValueError: If google_sheet_credentials_filename is not configured
        """
        if not self.google_sheet_credentials_filename:
            raise ValueError("Google Sheet credentials filename not configured")
        return self.app_root / self.credentials_folder / self.google_sheet_credentials_filename

    @property
    def static_path(self) -> Path:
        """Get full absolute path to static files folder.

        Returns:
            Path object pointing to the static files directory
        """
        return self.app_root / self.static_files_folder

    def validate(self) -> None:
        """Validate that all required configuration is present and valid.

        Checks that:
        - GOOGLE_SHEET_CREDENTIALS_FILENAME is configured
        - WORKBOOK_URL is configured
        - Credentials file exists at the specified path

        Raises:
            ValueError: If required environment variables are missing
            FileNotFoundError: If credentials file doesn't exist

        Example:
            >>> config = AppConfig.from_env(Path.cwd())
            >>> try:
            ...     config.validate()
            ... except ValueError as e:
            ...     print(f"Configuration error: {e}")
        """
        if not self.google_sheet_credentials_filename:
            raise ValueError("GOOGLE_SHEET_CREDENTIALS_FILENAME environment variable is required")
        if not self.workbook_url:
            raise ValueError("WORKBOOK_URL environment variable is required")
        if not self.credentials_path.exists():
            raise FileNotFoundError(f"Credentials file not found at: {self.credentials_path}")
        logger.info("Configuration validation successful")


# Global configuration instance (will be set in main.py)
config: AppConfig | None = None
