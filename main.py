import locale
import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from nicegui import app, ui

import app.core.config as config_module
from app.core.config import AppConfig
from app.core.state_manager import state_manager
from app.services import pages, utils
from app.services.google_sheets import GoogleSheetService
from app.ui import home, logout, net_worth, styles, user

# === Configure logging ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# === Load environment and configure app ===
load_dotenv()
APP_ROOT = Path(__file__).parent

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


# Initialize global configuration
app_config: AppConfig = AppConfig.from_env(APP_ROOT)
# Update the module-level config instance
config_module.config = app_config

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
        .dock button.dock-active {
    position: relative;
}

.dock button.dock-active::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 25%;       /* centers a 50% wide line */
    width: 50%;
    height: 2px;
    background-color: currentColor; /* same color as text/icon */
    border-radius: 1px;             /* optional: slightly rounded */
}
</style>

<!-- DaisyUI (full build from CDN; Tailwind provided by NiceGUI) -->
<link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.css" rel="stylesheet" type="text/css" />

<style>
  /* ensure main content isn't hidden behind bottom nav on mobile */
  .main-content { padding-bottom: 4.5rem; } /* ~72px */
  .nav-icon { width: 20px; height: 20px; display:block; margin: 0 auto; }
  .btm-label { display:block; font-size:11px; margin-top:4px; color:inherit; }
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

# Configure NiceGUI with persistent storage secret
ui.run(
    port=app_config.app_port,
    favicon=app_config.static_path / "favicon" / "favicon.ico",
    root_path=app_config.root_path,
    storage_secret=get_or_create_storage_secret(),
)
ui.add_head_html(THEME_SCRIPT + HEAD_HTML, shared=True)

# Initialize Google Sheets service
sheet_service = None
try:
    sheet_service = GoogleSheetService(app_config.credentials_path, app_config.workbook_url)
except Exception as e:
    logger.critical(f"Fatal startup error: {e}")
    ui.label(f"Application failed to start: {str(e)}").classes("text-red-500 font-bold")


def ensure_theme_setup():
    """Helper function to set up echarts theme based on saved theme."""
    # Check if this is the first time setup (no theme in storage)
    is_first_setup = "theme" not in app.storage.user

    # Use saved theme from app.storage or fallback to default
    current_theme = app.storage.user.get("theme", app_config.default_theme)

    # Ensure the theme is valid
    if current_theme not in ["light", "dark"]:
        current_theme = app_config.default_theme

    # Always set necessary values for echarts
    app.storage.user["theme"] = current_theme
    app.storage.user["echarts_theme_url"] = (
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


@ui.page("/", title=app_config.title)
def root():
    """Root page that redirects to home after loading necessary data."""
    ensure_theme_setup()
    if sheet_service is None:
        ui.label("Sheet service not available.").classes("text-red-500")
        return
    # Load data sheets into user storage if not already present
    if not app.storage.user.get("data_sheet"):
        app.storage.user["data_sheet"] = sheet_service.get_worksheet_as_dataframe(
            app_config.data_sheet_name
        ).to_json(orient="split")
    if not app.storage.user.get("assets_sheet"):
        app.storage.user["assets_sheet"] = sheet_service.get_worksheet_as_dataframe(
            app_config.assets_sheet_name, header=[0, 1]
        ).to_json(orient="split")
    if not app.storage.user.get("liabilities_sheet"):
        app.storage.user["liabilities_sheet"] = sheet_service.get_worksheet_as_dataframe(
            app_config.liabilities_sheet_name, header=[0, 1]
        ).to_json(orient="split")
    if not app.storage.user.get("expenses_sheet"):
        app.storage.user["expenses_sheet"] = sheet_service.get_worksheet_as_dataframe(
            app_config.expenses_sheet_name
        ).to_json(orient="split")
    # Detect client device type for responsive UI
    client = ui.context.client
    if not client or not client.request:
        ui.label("Client request not available.").classes("text-red-500")
        return
    user_agent_header = client.request.headers.get("user-agent")
    app.storage.client["user_agent"] = utils.get_user_agent(user_agent_header)
    ui.navigate.to("/home")


@ui.page(pages.HOME_PAGE, title=app_config.title)
def home_page():
    """Main dashboard page showing financial overview."""
    ensure_theme_setup()
    home.render()


@ui.page(pages.NET_WORTH_PAGE, title=app_config.title)
def net_worth_page():
    """Net worth tracking page with historical data."""
    ensure_theme_setup()
    net_worth.render()


@ui.page(pages.USER_PAGE, title=app_config.title)
def user_page():
    """User settings and preferences page."""
    ensure_theme_setup()
    user.render()


@ui.page(pages.LOGOUT_PAGE, title=app_config.title)
def logout_page():
    """Logout page for clearing user session."""
    ensure_theme_setup()
    logout.render()


@app.post("/api/sync-theme")
async def sync_theme(request):
    """API endpoint to synchronize theme changes from client-side."""
    try:
        data = await request.json()
        theme = data.get("theme", app_config.default_theme)
        # Validate and update theme if valid
        if theme in ["light", "dark"]:
            app.storage.user["theme"] = theme
            app.storage.user["echarts_theme_url"] = (
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
