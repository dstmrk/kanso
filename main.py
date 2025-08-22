import json
import os
import secrets
from functools import wraps

from nicegui import ui, app
from dotenv import load_dotenv
from pathlib import Path

from app.services.google_sheets import GoogleSheetService
from app.services import utils, pages
from app.ui import home, net_worth, user, styles, logout

# === Load environment ===
load_dotenv()
APP_ROOT = Path(__file__).parent
CREDENTIALS_FOLDER = "config/credentials"
CREDENTIALS_FILENAME = os.getenv("GOOGLE_SHEET_CREDENTIALS_FILENAME")
WORKBOOK_ID = os.getenv("WORKBOOK_ID")
DATA_SHEET_NAME = os.getenv("DATA_SHEET_NAME", "Data")
EXPENSES_SHEET_NAME = os.getenv("EXPENSES_SHEET_NAME", "Expenses")
DEFAULT_THEME = "light"
PORT = int(os.getenv("APP_PORT", 6789))
ROOT_PATH = os.getenv("ROOT_PATH", "")
TITLE = "kanso - your minimal money tracker"

THEME_SCRIPT = """
<script>
  (function() {
    // La chiave semplice che abbiamo definito in Python
    const key = 'theme_for_js'; 
    const storedTheme = localStorage.getItem(key);
    let theme = '""" + DEFAULT_THEME + """'; // Default se non troviamo nulla

    if (storedTheme) {
      try {
        // I valori in localStorage sono sempre stringhe, e NiceGUI usa JSON.
        // Esempio: 'dark' viene salvato come '"dark"'.
        theme = JSON.parse(storedTheme);
      } catch (e) {
        console.error('Errore nel parsing del tema:', e);
      }
    }
    // Imposta il tema prima che il <body> venga disegnato
    document.documentElement.setAttribute('data-theme', theme);
  })();
</script>
"""

HEAD_HTML = """
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
            
static_files_folder = APP_ROOT / 'static'
app.add_static_files('/themes', static_files_folder / 'themes')
app.add_static_files('/favicon', static_files_folder / 'favicon')
ui.run(port=PORT, favicon=static_files_folder / "favicon" / "favicon.ico", root_path = ROOT_PATH, storage_secret=secrets.token_urlsafe(32))
ui.add_head_html(THEME_SCRIPT + HEAD_HTML, shared=True)
try:
    if not CREDENTIALS_FILENAME or not WORKBOOK_ID:
        raise ValueError("Missing required environment variables")
    sheet_service = GoogleSheetService(APP_ROOT / CREDENTIALS_FOLDER / CREDENTIALS_FILENAME, WORKBOOK_ID)
except Exception as e:
    print(f"!!! FATAL STARTUP ERROR: {e} !!!")
    ui.label(f"Application failed to start: {str(e)}").classes("text-red-500 font-bold")
    
def apply_theme(func):
    """
    Un decoratore che legge il tema dallo storage e lo applica
    prima di eseguire la funzione della pagina.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        theme = app.storage.user.get('theme', DEFAULT_THEME)
        ui.run_javascript(f"""document.documentElement.setAttribute('data-theme', '{theme}');""")
        app.storage.user['theme'] = theme
        app.storage.user['echarts_theme_url'] = styles.DEFAULT_ECHART_THEME_FOLDER + theme + styles.DEFAULT_ECHARTS_THEME_SUFFIX
        result = func(*args, **kwargs)
        return result
    return wrapper

@ui.page('/', title=TITLE)
@apply_theme
def root():
        if not app.storage.user.get('data_sheet'):
          app.storage.user['data_sheet'] = sheet_service.get_worksheet_as_dataframe(DATA_SHEET_NAME).to_json(orient='split')
        if not app.storage.user.get('expenses_sheet'):
          app.storage.user['expenses_sheet'] = sheet_service.get_worksheet_as_dataframe(EXPENSES_SHEET_NAME).to_json(orient='split')
        client = ui.context.client
        if not client or not client.request:
            ui.label("Client request not available.").classes("text-red-500")
            return
        app.storage.client["user_agent"] = utils.get_user_agent(client.request.headers.get('user-agent'))
        ui.navigate.to('/home')
        
@ui.page(pages.HOME_PAGE, title = TITLE)
@apply_theme
def home_page():
    home.render()
    
@ui.page(pages.NET_WORTH_PAGE, title = TITLE)
@apply_theme
def net_worth_page():
    net_worth.render()

@ui.page(pages.USER_PAGE, title = TITLE)
@apply_theme
def user_page():
    user.render()

@ui.page(pages.LOGOUT_PAGE, title= TITLE)
@apply_theme
def logout_page():
    logout.render()