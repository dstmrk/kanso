
import gspread
from app.utils import load_env

GSHEET_CREDENTIAL_PATH_KEY = "GOOGLE_SHEET_CREDENTIAL_PATH"
WORKBOOK_ID_KEY = "WORKBOOK_ID"
DATA_SHEET_NAME_KEY = "DATA_SHEET_NAME"

def get_sheet_data():
    google_sheet_credentials_path = load_env(GSHEET_CREDENTIAL_PATH_KEY)
    workbook_id = load_env(WORKBOOK_ID_KEY)
    data_sheet_name = load_env(DATA_SHEET_NAME_KEY)
    gc = gspread.service_account(filename=google_sheet_credentials_path)
    sh = gc.open_by_key(workbook_id)
    ws = sh.worksheet(data_sheet_name)
    data = ws.get_all_values()
    return data