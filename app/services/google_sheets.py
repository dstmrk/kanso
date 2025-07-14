# app/services/google_sheets.py
import gspread
import pandas as pd
from pathlib import Path

class GoogleSheetService:
    def __init__(self, credentials_path: str, workbook_id: str):
        self.creds_path = Path(credentials_path)
        self.workbook_id = workbook_id
        if not self.creds_path.exists():
            raise FileNotFoundError(f"Credentials file not found at: {self.creds_path}")
        self.client = self._authenticate()

    def _authenticate(self):
        """Authenticates with Google Sheets using service account."""
        return gspread.service_account(filename=str(self.creds_path))

    def get_worksheet_as_dataframe(self, worksheet_name: str) -> pd.DataFrame:
        """Fetches a specific worksheet and returns it as a pandas DataFrame."""
        try:
            sheet = self.client.open_by_key(self.workbook_id).worksheet(worksheet_name)
            # Get all records from the sheet and convert to DataFrame
            data = sheet.get_all_records()
            return pd.DataFrame(data)
        except gspread.exceptions.WorksheetNotFound:
            print(f"Error: Worksheet '{worksheet_name}' not found in '{self.workbook_id}'.")
            return pd.DataFrame() # Return empty dataframe on error