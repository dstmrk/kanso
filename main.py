import os
import secrets
import pandas as pd

from io import StringIO
from nicegui import ui, app
from dotenv import load_dotenv
from pathlib import Path
from user_agents import parse

from app.services.google_sheets import GoogleSheetService
from app.logic import finance_calculator
from app.ui import dashboard_page

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

# === Utilities ===
def get_user_agent(http_agent: str | None) -> str:
    return "mobile" if http_agent and parse(http_agent).is_mobile else "desktop"

def get_or_store(key: str, compute_fn):
    if key not in app.storage.user:
        app.storage.user[key] = compute_fn()
    return app.storage.user[key]

# === Page ===
@ui.page('/', title='Kanso - Your Minimal Money Tracker')
def main_page():
    try:
        if not CREDENTIALS_FILENAME or not WORKBOOK_ID:
            raise ValueError("Missing required environment variables")

        # Initialize Google Sheets service
        sheet_service = GoogleSheetService(APP_ROOT / CREDENTIALS_FOLDER / CREDENTIALS_FILENAME, WORKBOOK_ID)

        # Load data sheets (with cache in user storage)
        data_sheet_json = get_or_store('data_sheet', lambda: sheet_service.get_worksheet_as_dataframe(DATA_SHEET_NAME).to_json(orient='split'))
        expenses_sheet_json = get_or_store('expenses_sheet', lambda: sheet_service.get_worksheet_as_dataframe(EXPENSES_SHEET_NAME).to_json(orient='split'))

        data_sheet = pd.read_json(StringIO(data_sheet_json), orient='split')
        expenses_sheet = pd.read_json(StringIO(expenses_sheet_json), orient='split')

        # Compute or retrieve metrics
        net_worth = get_or_store('current_net_worth', lambda: finance_calculator.get_current_net_worth(data_sheet))
        mom_variation = get_or_store('mom_variation', lambda: finance_calculator.get_month_over_month_net_worth_variation(data_sheet))
        avg_saving_ratio = get_or_store('avg_saving_ratio', lambda: finance_calculator.get_average_saving_ratio_last_12_months(data_sheet))
        fi_progress = get_or_store('fi_progress', lambda: finance_calculator.get_fi_progress(data_sheet))
        net_worth_data = get_or_store('net_worth_data', lambda: finance_calculator.get_monthly_net_worth(data_sheet))
        asset_vs_liabilities_data = get_or_store('assets_vs_liabilities_data', lambda: finance_calculator.get_assets_liabilities(data_sheet))
        incomes_vs_expenses = get_or_store('incomes_vs_expenses_data', lambda: finance_calculator.get_incomes_vs_expenses(data_sheet))
        cash_flow_data = get_or_store('cash_flow_data', lambda: finance_calculator.get_cash_flow_last_12_months(data_sheet, expenses_sheet))
        avg_expenses = get_or_store('avg_expenses', lambda: finance_calculator.get_average_expenses_by_category_last_12_months(expenses_sheet))

        # Store theme once (doesn't depend on user data)
        app.storage.user.setdefault('theme_url', THEME_FILENAME)

        # Get user agent
        client = ui.context.client
        if not client or not client.request:
            ui.label("Client request not available.").classes("text-red-500")
            return
        user_agent = get_user_agent(client.request.headers.get('user-agent'))
        app.storage.client["user_agent"] = user_agent

        # Render dashboard
        dashboard_page.create_page(
            net_worth_data,
            asset_vs_liabilities_data,
            incomes_vs_expenses,
            cash_flow_data,
            avg_expenses,
            net_worth,
            mom_variation,
            avg_saving_ratio,
            fi_progress,
            app.storage.user["theme_url"],
            user_agent
        )

    except Exception as e:
        print(f"!!! FATAL STARTUP ERROR: {e} !!!")
        ui.label(f"Application failed to start: {str(e)}").classes("text-red-500 font-bold")

# === Static assets and app run ===
static_files_folder = APP_ROOT / 'static'
app.add_static_files('/themes', static_files_folder / 'themes')
app.add_static_files('/favicon', static_files_folder / 'favicon')

ui.run(port=PORT, favicon=static_files_folder / "favicon" / "favicon.ico", storage_secret=secrets.token_urlsafe(32))
