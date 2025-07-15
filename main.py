# main.py
import os
from nicegui import ui, app
from dotenv import load_dotenv
from pathlib import Path

from app.services.google_sheets import GoogleSheetService
from app.logic import finance_calculator
from app.ui import dashboard_page

load_dotenv()
APP_ROOT = Path(__file__).parent
CREDENTIALS_PATH = os.getenv("GOOGLE_SHEET_CREDENTIAL_PATH")
WORKBOOK_ID = os.getenv("WORKBOOK_ID")
DATA_SHEET_NAME = os.getenv("DATA_SHEET_NAME")
THEME_URL = os.getenv("ECHARTS_THEME_URL")
PORT = os.getenv("APP_PORT") or 6789
PORT = int(PORT)

static_files_path = APP_ROOT / 'static' / 'themes'
app.add_static_files('/themes', static_files_path)

async def on_startup():
    try:
        print("--- Loading Google Sheet data ---")
        if CREDENTIALS_PATH is None:
            raise ValueError("CREDENTIALS_PATH environment variable not set.")
        if WORKBOOK_ID is None:
            raise ValueError("GOOGLE_SHEET_NAME environment variable not set.")
        if DATA_SHEET_NAME is None:
            raise ValueError("DATA_SHEET_NAME environment variable not set.")
        sheet_service = GoogleSheetService(APP_ROOT / CREDENTIALS_PATH, WORKBOOK_ID)
        net_worth_raw_df = sheet_service.get_worksheet_as_dataframe(DATA_SHEET_NAME)
        processed_net_worth = finance_calculator.get_monthly_net_worth(net_worth_raw_df)
        app.storage.general['net_worth_data'] = processed_net_worth
        print("--- Data loaded successfully ---")
    except Exception as e:
        print(f"!!! FATAL STARTUP ERROR: {e} !!!")
        app.storage.general['startup_error'] = str(e)

app.on_startup(on_startup)

@ui.page('/', title='My Personal Finance Dashboard', favicon='💰')
def main_page():
    if 'startup_error' in app.storage.general:
        error_message = app.storage.general['startup_error']
        ui.label(f"Application failed to start: {error_message}").classes("text-red-500 font-bold")
        return
    
    net_worth_data = app.storage.general.get('net_worth_data')
    if not net_worth_data or not net_worth_data['dates']:
        ui.label("No Net Worth data could be loaded or processed.").classes("text-orange-500")
        return
    dashboard_page.create_page(net_worth_data, THEME_URL)

ui.run(port=PORT)