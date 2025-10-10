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


@dataclass
class AppConfig:
    """Centralized application configuration."""

    # File paths
    app_root: Path
    credentials_folder: str = "config/credentials"
    static_files_folder: str = "static"

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
    storage_secret: str | None = None

    # Cache settings (for data that updates monthly)
    cache_ttl_seconds: int = CACHE_TTL_SECONDS

    @classmethod
    def from_env(cls, app_root: Path) -> "AppConfig":
        """Create configuration from environment variables."""
        config = cls(
            app_root=app_root,
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
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", str(CACHE_TTL_SECONDS))),
        )
        logger.info(
            f"Configuration loaded: port={config.app_port}, theme={config.default_theme}, cache_ttl={config.cache_ttl_seconds}s"
        )
        return config

    @property
    def credentials_path(self) -> Path:
        """Get full path to credentials file."""
        if not self.google_sheet_credentials_filename:
            raise ValueError("Google Sheet credentials filename not configured")
        return self.app_root / self.credentials_folder / self.google_sheet_credentials_filename

    @property
    def static_path(self) -> Path:
        """Get full path to static files folder."""
        return self.app_root / self.static_files_folder

    def validate(self) -> None:
        """Validate required configuration."""
        if not self.google_sheet_credentials_filename:
            raise ValueError("GOOGLE_SHEET_CREDENTIALS_FILENAME environment variable is required")
        if not self.workbook_url:
            raise ValueError("WORKBOOK_URL environment variable is required")
        if not self.credentials_path.exists():
            raise FileNotFoundError(f"Credentials file not found at: {self.credentials_path}")
        logger.info("Configuration validation successful")


# Global configuration instance (will be set in main.py)
config: AppConfig | None = None
