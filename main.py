import locale
import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from nicegui import app, ui

import app.core.config as config_module
from app.core.config import AppConfig
from app.core.monitoring import metrics_collector
from app.core.state_manager import state_manager
from app.services import pages, utils
from app.services.google_sheets import GoogleSheetService
from app.ui import expenses, home, logout, net_worth, onboarding, settings, styles

# === Load environment first ===
APP_ROOT = Path(__file__).parent

# Auto-load environment-specific files
# Priority: .env.{env} < .env.{env}.local < explicitly set env vars
env = os.getenv("APP_ENV", "dev")  # Default to dev for local development
env_file = APP_ROOT / f".env.{env}"
env_file_local = APP_ROOT / f".env.{env}.local"

if env_file.exists():
    load_dotenv(env_file)
    print(f"✓ Loaded environment from: {env_file.name}")
else:
    print(f"⚠ Environment file not found: {env_file.name}")
    print(f"  Expected: {env_file}")
    print(f"  Hint: Copy .env.dev to .env.{env} or set APP_ENV=dev")

if env_file_local.exists():
    load_dotenv(env_file_local, override=True)
    print(f"✓ Loaded local overrides from: {env_file_local.name}")

# Initialize global configuration
app_config: AppConfig = AppConfig.from_env(APP_ROOT)
# Update the module-level config instance
config_module.config = app_config


# === Configure logging with colors ===
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        """Format log record with color-coded log levels.

        Args:
            record: LogRecord instance containing log information

        Returns:
            Formatted log message string with color codes
        """
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


# Set up root logger with colored formatter
handler = logging.StreamHandler()
handler.setFormatter(
    ColoredFormatter(
        # Format: LEVEL: timestamp - logger_name - message (uniform with Uvicorn)
        # -8s adds padding to align log levels (max 8 chars for "CRITICAL")
        # Colon followed by 4 spaces matches Uvicorn's format
        fmt="%(levelname)-8s: %(asctime)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)

root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, app_config.log_level))
root_logger.addHandler(handler)

# Configure Uvicorn loggers to use our formatter
for uvicorn_logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
    uvicorn_logger = logging.getLogger(uvicorn_logger_name)
    uvicorn_logger.handlers = []  # Remove default handlers
    uvicorn_logger.addHandler(handler)  # Use our colored handler
    uvicorn_logger.propagate = False  # Don't propagate to root

logger = logging.getLogger(__name__)

# Storage secret management - persist across app restarts
STORAGE_SECRET_FILE = APP_ROOT / ".storage_secret"


def get_or_create_storage_secret():
    """Get existing storage secret or create a new one if it doesn't exist."""
    if STORAGE_SECRET_FILE.exists():
        try:
            with open(STORAGE_SECRET_FILE) as f:
                secret = f.read().strip()
                if secret:  # Ensure it's not empty
                    return secret
        except OSError:
            pass  # Fall through to create new secret

    # Create new secret and save it
    secret = secrets.token_urlsafe(32)
    try:
        with open(STORAGE_SECRET_FILE, "w") as f:
            f.write(secret)
        # Make file readable only by owner for security
        os.chmod(STORAGE_SECRET_FILE, 0o600)
    except OSError as e:
        logger.warning(f"Could not save storage secret to file: {e}")

    return secret


THEME_SCRIPT: str = f"""
<script>
  (function() {{
    const storedTheme = localStorage.getItem('kanso-theme');
    const theme = storedTheme || '{app_config.default_theme}';
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.style.colorScheme = theme;

    // Ensure localStorage has the theme value if it was missing
    if (!storedTheme) {{
      localStorage.setItem('kanso-theme', theme);
    }}
  }})();
</script>
"""

HEAD_HTML: str = """
<link rel="apple-touch-icon" sizes="180x180" href="/favicon/apple-touch-icon.png" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style> body { font-family: 'Inter', sans-serif; }
</style>

<!-- DaisyUI (full build from CDN; Tailwind provided by NiceGUI) -->
<link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.css" rel="stylesheet" type="text/css" />

<style>

  /* Remove scroll from tab panels (NiceGUI adds .scroll class automatically) */
  .q-tab-panels .q-panel.scroll {
    overflow: visible !important;
    max-height: none !important;
    height: auto !important;
  }
</style>
"""

# === Initialize application ===
locale.setlocale(locale.LC_ALL, "")

# Validate configuration and setup paths
try:
    app_config.validate()
except (ValueError, FileNotFoundError) as e:
    logger.error(f"Configuration error: {e}")
    ui.label(f"Application configuration error: {str(e)}").classes("text-red-500 font-bold")

# Setup static files
app.add_static_files("/themes", app_config.static_path / "themes")
app.add_static_files("/favicon", app_config.static_path / "favicon")

# Add head HTML for theme and styling
ui.add_head_html(THEME_SCRIPT + HEAD_HTML, shared=True)

# Google Sheets service - will be initialized from user storage
sheet_service = None


def get_sheet_service():
    """Get or create GoogleSheetService with credentials from general storage (shared across devices)."""
    global sheet_service
    import json
    import tempfile
    from pathlib import Path

    # Check for credentials and URL in general storage
    if hasattr(app, "storage") and hasattr(app.storage, "general"):
        custom_creds_json = app.storage.general.get("google_credentials_json")
        custom_url = app.storage.general.get("custom_workbook_url")

        # Use credentials if both are available
        if custom_creds_json and custom_url:
            try:
                # Create a temporary file with the credentials (will be auto-deleted)
                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=True) as tmp:
                    json.dump(json.loads(custom_creds_json), tmp, indent=2)
                    tmp.flush()  # Ensure data is written
                    tmp_path = Path(tmp.name)

                    # Initialize with credentials from storage
                    sheet_service = GoogleSheetService(tmp_path, custom_url)
                    logger.info("Using credentials and workbook URL from general storage")
                # File is automatically deleted when exiting the 'with' block
                return sheet_service
            except Exception as e:
                logger.error(f"Failed to use credentials from storage: {e}")
                raise RuntimeError(f"Failed to initialize Google Sheets service: {e}") from e

    # No credentials configured
    raise RuntimeError("Google Sheets not configured. Please complete the onboarding setup.")


def ensure_theme_setup():
    """Helper function to set up echarts theme based on saved theme."""
    # Check if this is the first time setup (no theme in general storage)
    is_first_setup = "theme" not in app.storage.general

    # Use saved theme from app.storage.general or fallback to default
    current_theme = app.storage.general.get("theme", app_config.default_theme)

    # Ensure the theme is valid
    if current_theme not in ["light", "dark"]:
        current_theme = app_config.default_theme

    # Always set necessary values for echarts in general storage (shared across devices)
    app.storage.general["theme"] = current_theme
    app.storage.general["echarts_theme_url"] = (
        styles.DEFAULT_ECHART_THEME_FOLDER + current_theme + styles.DEFAULT_ECHARTS_THEME_SUFFIX
    )

    # Sync theme between server storage and client localStorage
    if is_first_setup:
        # First setup: ensure localStorage matches our default theme
        ui.run_javascript(
            f"""
            localStorage.setItem('kanso-theme', '{current_theme}');
            document.documentElement.setAttribute('data-theme', '{current_theme}');
            document.documentElement.style.colorScheme = '{current_theme}';
        """
        )
    else:
        # Normal sync: check if client and server are aligned
        ui.run_javascript(
            f"""
            const currentTheme = localStorage.getItem('kanso-theme') || '{app_config.default_theme}';
            if (currentTheme !== '{current_theme}') {{
                // If there's a difference, update the server asynchronously
                fetch('/api/sync-theme', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ theme: currentTheme }})
                }}).catch(() => {{
                    console.debug('Background theme sync failed');
                }});
            }}
        """
        )


# === Page Definitions ===
# All pages must be defined before ui.run() is called to ensure they are registered


@ui.page("/", title=app_config.title)
def root():
    """Root page that checks onboarding status and redirects."""
    ensure_theme_setup()

    # Check if onboarding is completed (in general storage, shared across devices)
    if not app.storage.general.get("onboarding_completed"):
        ui.navigate.to("/onboarding")
        return

    # Detect client device type for responsive UI
    client = ui.context.client
    if client and client.request:
        user_agent_header = client.request.headers.get("user-agent")
        app.storage.client["user_agent"] = utils.get_user_agent(user_agent_header)

    # Redirect directly to home - data will be loaded lazily
    ui.navigate.to("/home")


@ui.page("/onboarding", title=f"{app_config.title} - Setup")
def onboarding_page():
    """Onboarding page for first-time setup."""
    ensure_theme_setup()
    onboarding.render()


@ui.page(pages.HOME_PAGE, title=app_config.title)
def home_page():
    """Main dashboard page showing financial overview."""
    ensure_theme_setup()

    # Render home immediately with placeholders
    # Data will be loaded asynchronously in the background
    home.render()


@ui.page(pages.EXPENSES_PAGE, title=app_config.title)
def expenses_page():
    """Expenses page showing transaction details and category breakdown."""
    ensure_theme_setup()
    expenses.render()


@ui.page(pages.NET_WORTH_PAGE, title=app_config.title)
def net_worth_page():
    """Net worth tracking page with historical data."""
    ensure_theme_setup()
    net_worth.render()


@ui.page(pages.SETTINGS_PAGE, title=app_config.title)
def settings_page():
    """Settings page with tabs for Account, Data, and About."""
    ensure_theme_setup()
    settings.render()


@ui.page(pages.LOGOUT_PAGE, title=app_config.title)
def logout_page():
    """Logout page for clearing user session."""
    ensure_theme_setup()
    logout.render()


# === API Endpoints ===


@app.post("/api/sync-theme")
async def sync_theme(request):
    """API endpoint to synchronize theme changes from client-side."""
    try:
        data = await request.json()
        theme = data.get("theme", app_config.default_theme)
        # Validate and update theme if valid (in general storage - shared across devices)
        if theme in ["light", "dark"]:
            app.storage.general["theme"] = theme
            app.storage.general["echarts_theme_url"] = (
                styles.DEFAULT_ECHART_THEME_FOLDER + theme + styles.DEFAULT_ECHARTS_THEME_SUFFIX
            )
            logger.debug(f"Theme synced to: {theme}")
        return {"status": "success", "theme": theme}
    except Exception as e:
        logger.error(f"Theme sync error: {e}")
        return {"status": "error"}


@app.get("/api/cache-stats")
async def cache_stats():
    """Get cache statistics for debugging and monitoring."""
    return state_manager.get_cache_stats()


@app.post("/api/cache-clear")
async def clear_cache():
    """Clear cache manually (useful for development)."""
    state_manager.invalidate_cache()
    return {"status": "success", "message": "Cache cleared"}


@app.get("/api/metrics")
async def get_metrics():
    """Get performance metrics and statistics."""
    return metrics_collector.get_statistics()


@app.post("/api/metrics/save")
async def save_metrics():
    """Save current metrics to file."""
    metrics_file = APP_ROOT / "metrics" / "app_metrics.json"
    metrics_collector.save_to_file(metrics_file)
    return {"status": "success", "message": f"Metrics saved to {metrics_file}"}


@app.post("/api/metrics/reset")
async def reset_metrics():
    """Reset all collected metrics."""
    metrics_collector.reset()
    return {"status": "success", "message": "Metrics reset"}


# Save metrics on shutdown
@app.on_shutdown
async def save_metrics_on_shutdown():
    """Save metrics to file when the application shuts down."""
    metrics_file = APP_ROOT / "metrics" / "app_metrics.json"
    metrics_collector.save_to_file(metrics_file)
    logger.info("Metrics saved on application shutdown")


# === Start Server ===
# This should be the last code in the file
# Use __mp_main__ to support multiprocessing (used by NiceGUI's reload feature)
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        port=app_config.app_port,
        favicon=app_config.static_path / "favicon" / "favicon.ico",
        root_path=app_config.root_path,
        storage_secret=get_or_create_storage_secret(),
        reload=app_config.reload,
        uvicorn_logging_level=app_config.uvicorn_log_level,
        show_welcome_message=app_config.debug,
        # Disable HTTP access logs for cleaner output (they use different format)
        # If needed, can be re-enabled with: access_log=True
        access_log=False,
    )
