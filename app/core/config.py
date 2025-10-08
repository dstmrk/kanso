import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

@dataclass
class AppConfig:
    """Centralized application configuration."""
    
    # File paths
    app_root: Path
    credentials_folder: str = "config/credentials"
    static_files_folder: str = "static"
    
    # Google Sheets
    google_sheet_credentials_filename: Optional[str] = None
    workbook_id: Optional[str] = None
    data_sheet_name: str = "Data"
    assets_sheet_name: str = "Assets"
    liabilities_sheet_name: str = "Liabilities"
    expenses_sheet_name: str = "Expenses"
    
    # App settings
    app_port: int = 6789
    root_path: str = ""
    title: str = "kanso - your minimal money tracker"
    default_theme: str = "light"
    storage_secret: Optional[str] = None
    
    # Cache settings (for data that updates monthly)
    cache_ttl_seconds: int = 86400  # 24 hours - since data updates monthly
    
    @classmethod
    def from_env(cls, app_root: Path) -> 'AppConfig':
        """Create configuration from environment variables."""
        return cls(
            app_root=app_root,
            credentials_folder=os.getenv("CREDENTIALS_FOLDER", "config/credentials"),
            static_files_folder=os.getenv("STATIC_FILES_FOLDER", "static"),
            google_sheet_credentials_filename=os.getenv("GOOGLE_SHEET_CREDENTIALS_FILENAME"),
            workbook_id=os.getenv("WORKBOOK_ID"),
            data_sheet_name=os.getenv("DATA_SHEET_NAME", "Data"),
            assets_sheet_name=os.getenv("ASSETS_SHEET_NAME", "Assets"),
            liabilities_sheet_name=os.getenv("LIABILITIES_SHEET_NAME", "Liabilities"),
            expenses_sheet_name=os.getenv("EXPENSES_SHEET_NAME", "Expenses"),
            app_port=int(os.getenv("APP_PORT", "6789")),
            root_path=os.getenv("ROOT_PATH", ""),
            title=os.getenv("APP_TITLE", "kanso - your minimal money tracker"),
            default_theme=os.getenv("DEFAULT_THEME", "light"),
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "86400"))
        )
    
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
        if not self.workbook_id:
            raise ValueError("WORKBOOK_ID environment variable is required")
        if not self.credentials_path.exists():
            raise FileNotFoundError(f"Credentials file not found at: {self.credentials_path}")

# Global configuration instance (will be set in main.py)
config: Optional[AppConfig] = None