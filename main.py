import os
from nicegui import ui, app
from dotenv import load_dotenv
from pathlib import Path

from app.services.google_sheets import GoogleSheetService
from app.logic import finance_calculator
from app.ui import dashboard_page

load_dotenv()
APP_ROOT = Path(__file__).parent
CREDENTIALS_FOLDER = "config/credentials"
CREDENTIALS_FILENAME = os.getenv("GOOGLE_SHEET_CREDENTIALS_FILENAME")
WORKBOOK_ID = os.getenv("WORKBOOK_ID")
DATA_SHEET_NAME = os.getenv("DATA_SHEET_NAME") or "Data"
EXPENSES_SHEET_NAME = os.getenv("EXPENSES_SHEET_NAME") or "Expenses"
THEME_FILENAME = "themes/" + (os.getenv("ECHARTS_THEME_URL") or "default_echarts_theme.json")
PORT = os.getenv("APP_PORT") or 6789
PORT = int(PORT)

static_files_folder = APP_ROOT / 'static'
static_theme_files_path = static_files_folder / 'themes'
static_favicon_files_path = static_files_folder / 'favicon'
app.add_static_files('/themes', static_theme_files_path)
app.add_static_files('/favicon', static_favicon_files_path)

async def on_startup():
    try:
        if CREDENTIALS_FILENAME is None:
            raise ValueError("CREDENTIALS_PATH environment variable not set.")
        if WORKBOOK_ID is None:
            raise ValueError("GOOGLE_SHEET_NAME environment variable not set.")
        if DATA_SHEET_NAME is None:
            raise ValueError("DATA_SHEET_NAME environment variable not set.")
        if EXPENSES_SHEET_NAME is None:
            raise ValueError("EXPENSES_SHEET_NAME environment variable not set.")
        print("--- Loading Google Sheet data ---")
        sheet_service = GoogleSheetService(APP_ROOT / CREDENTIALS_FOLDER / CREDENTIALS_FILENAME, WORKBOOK_ID)
        data_sheet = sheet_service.get_worksheet_as_dataframe(DATA_SHEET_NAME)
        print("--- Data loaded successfully ---")
        print("--- Extracting Data ---")
        app.storage.general['current_net_worth'] = finance_calculator.get_current_net_worth(data_sheet)
        app.storage.general['mom_variation'] = finance_calculator.get_month_over_month_net_worth_variation(data_sheet)
        app.storage.general['avg_saving_ratio'] = finance_calculator.get_average_saving_ratio_last_12_months(data_sheet)
        app.storage.general['fi_progress'] = finance_calculator.get_fi_progress(data_sheet)
        app.storage.general['net_worth_data'] = finance_calculator.get_monthly_net_worth(data_sheet)
        app.storage.general['assets_vs_liabilities_data'] = finance_calculator.get_assets_liabilities(data_sheet)
        app.storage.general['incomes_vs_expenses_data'] = finance_calculator.get_incomes_vs_expenses(data_sheet)
        print("--- Data extracted successfully ---")
        print("--- Loading Google Sheet expenses ---")
        expenses_sheet = sheet_service.get_worksheet_as_dataframe(EXPENSES_SHEET_NAME)
        print("--- Expenses loaded successfully ---")
        app.storage.general['cash_flow_data'] = finance_calculator.get_cash_flow_last_12_months(data_sheet, expenses_sheet)
        app.storage.general['avg_expenses'] = finance_calculator.get_average_expenses_by_category_last_12_months(expenses_sheet)
        app.storage.general['theme_url'] = THEME_FILENAME
    except Exception as e:
        print(f"!!! FATAL STARTUP ERROR: {e} !!!")
        app.storage.general['startup_error'] = str(e)

def get_user_agent(http_agent: str) -> str:
    user_agent = "desktop"
    if "mobile" in http_agent.lower():
        user_agent = "mobile"
    return user_agent

app.on_startup(on_startup)

@ui.page('/', title='Kanso - your minimal money tracker')
def main_page():
    if 'startup_error' in app.storage.general:
        error_message = app.storage.general['startup_error']
        ui.label(f"Application failed to start: {error_message}").classes("text-red-500 font-bold")
        del app.storage.general['startup_error']
        return
    
    net_worth =  app.storage.general['current_net_worth']
    if not net_worth:
        ui.label("No Net Worth data could be loaded or processed.").classes("text-orange-500")
        return
    
    mom_variation = app.storage.general['mom_variation']
    if not mom_variation:
        ui.label("No Month Over Month Variation could be loaded or processed.").classes("text-orange-500")
        return
    
    avg_saving_ratio = app.storage.general['avg_saving_ratio']
    if not avg_saving_ratio:
        ui.label("No Average Saving Ratio could be loaded or processed.").classes("text-orange-500")
        return

    fi_progress = app.storage.general['fi_progress']
    if not fi_progress:
        ui.label("No Financial Independence Progress could be loaded or processed.").classes("text-orange-500")
        return
    
    net_worth_data = app.storage.general.get('net_worth_data')
    if not net_worth_data or not net_worth_data['dates']:
        ui.label("No Net Worth data could be loaded or processed.").classes("text-orange-500")
        return
    
    asset_vs_liabilities_data = app.storage.general.get('assets_vs_liabilities_data')
    if not asset_vs_liabilities_data:
        ui.label("No Assets Vs Liabilities data could be loaded or processed.").classes("text-orange-500")
        return
    
    cash_flow_data = app.storage.general.get('cash_flow_data')
    if not cash_flow_data:
        ui.label("No Cash Flow data could be loaded or processed.").classes("text-orange-500")
        return
    
    avg_expenses = app.storage.general.get('avg_expenses')
    if not avg_expenses:
        ui.label("No Expenses data could be loaded or processed.").classes("text-orange-500")
        return
    
    incomes_vs_expenses =  app.storage.general.get('incomes_vs_expenses_data')
    if not incomes_vs_expenses:
        ui.label("No Income or Expenses data could be loaded or processed.").classes("text-orange-500")
        return
    
    client_request = ui.context.client.request
    if not client_request:
        ui.label("No Request found.").classes("text-orange-500")
        return
    
    theme_url = app.storage.general.get('theme_url')
    if not theme_url:
        theme_url = ""
        
    app.storage.client["user_agent"] = get_user_agent(client_request.headers['user-agent'])
    dashboard_page.create_page(net_worth_data, asset_vs_liabilities_data, incomes_vs_expenses, cash_flow_data, avg_expenses, net_worth, mom_variation, avg_saving_ratio, fi_progress, theme_url, app.storage.client["user_agent"])

ui.run(port=PORT, favicon= static_favicon_files_path / "favicon.ico")