import os
import secrets

from nicegui import ui, app
from dotenv import load_dotenv
from pathlib import Path

from app.services.google_sheets import GoogleSheetService
from app.services import utils, pages
from app.ui import home, net_worth

# === Load environment ===
load_dotenv()
APP_ROOT = Path(__file__).parent
CREDENTIALS_FOLDER = "config/credentials"
CREDENTIALS_FILENAME = os.getenv("GOOGLE_SHEET_CREDENTIALS_FILENAME")
WORKBOOK_ID = os.getenv("WORKBOOK_ID")
DATA_SHEET_NAME = os.getenv("DATA_SHEET_NAME", "Data")
EXPENSES_SHEET_NAME = os.getenv("EXPENSES_SHEET_NAME", "Expenses")
THEME_FILENAME = "themes/" + os.getenv("ECHARTS_THEME_URL", "default_echarts_theme.json")
PORT = int(os.getenv("APP_PORT", 6789))
TITLE = "kanso - your minimal money tracker"

HEAD_HTML = '''<link rel="preconnect" href="https://rsms.me/">
                <link rel="stylesheet" href="https://rsms.me/inter/inter.css">
                <style>
                body {
                        font-family: "Inter", Roboto, -apple-system, "Helvetica Neue", Helvetica, Arial, sans-serif;
                        background-color: #1C293A;
                        }
                </style>
            '''
            
static_files_folder = APP_ROOT / 'static'
app.add_static_files('/themes', static_files_folder / 'themes')
app.add_static_files('/favicon', static_files_folder / 'favicon')
ui.run(port=PORT, favicon=static_files_folder / "favicon" / "favicon.ico", storage_secret=secrets.token_urlsafe(32))
ui.add_head_html(HEAD_HTML, shared=True)
try:
    if not CREDENTIALS_FILENAME or not WORKBOOK_ID:
        raise ValueError("Missing required environment variables")
    sheet_service = GoogleSheetService(APP_ROOT / CREDENTIALS_FOLDER / CREDENTIALS_FILENAME, WORKBOOK_ID)
except Exception as e:
    print(f"!!! FATAL STARTUP ERROR: {e} !!!")
    ui.label(f"Application failed to start: {str(e)}").classes("text-red-500 font-bold")

@ui.page('/', title=TITLE)
def root():
        app.storage.user['data_sheet'] = sheet_service.get_worksheet_as_dataframe(DATA_SHEET_NAME).to_json(orient='split')
        app.storage.user['expenses_sheet'] = sheet_service.get_worksheet_as_dataframe(EXPENSES_SHEET_NAME).to_json(orient='split')
        app.storage.user.setdefault('theme_url', THEME_FILENAME)
        client = ui.context.client
        if not client or not client.request:
            ui.label("Client request not available.").classes("text-red-500")
            return
        app.storage.client["user_agent"] = utils.get_user_agent(client.request.headers.get('user-agent'))
        ui.navigate.to('/home')
        
@ui.page(pages.HOME_PAGE, title = TITLE)
def home_page():
    home.render()
    
@ui.page(pages.NET_WORTH_PAGE, title = TITLE)
def net_worth_page():
    net_worth.render()