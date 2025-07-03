import os
import gspread
from nicegui import ui
from dotenv import load_dotenv
load_dotenv()
google_sheet_credentials_path = os.getenv("GOOGLE_SHEET_CREDENTIAL_PATH")
workbook_id = os.getenv("WORKBOOK_ID")
data_sheet_name = os.getenv("DATA_SHEET_NAME")
gc = gspread.service_account(filename=google_sheet_credentials_path)
sh = gc.open_by_key(workbook_id)
ws = sh.worksheet(data_sheet_name)
list_of_lists = ws.get_all_values()
ui.table(rows=list_of_lists)
ui.run()
