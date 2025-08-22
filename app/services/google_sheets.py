import gspread
import pandas as pd
from pathlib import Path
from typing import List, Union

class GoogleSheetService:
    def __init__(self, credentials_path: Union[str, Path], workbook_id: str):
        self.creds_path = Path(credentials_path)
        self.workbook_id = workbook_id
        if not self.creds_path.exists():
            raise FileNotFoundError(f"Credentials file not found at: {self.creds_path}")
        self.client = self._authenticate()

    def _authenticate(self):
        return gspread.service_account(filename=str(self.creds_path))

    def get_worksheet_as_dataframe(self, worksheet_name: str, header: Union[int, List[int]] = 0, index_col: Union[int, None] = 0) -> pd.DataFrame:
        try:
            sheet = self.client.open_by_key(self.workbook_id).worksheet(worksheet_name)
            data = sheet.get_all_values()
            if not data:
                return pd.DataFrame()
            df = pd.DataFrame(data)
            df.columns = df.iloc[header]
            header_rows_to_drop = [header] if isinstance(header, int) else header
            df = df.drop(header_rows_to_drop)
            if index_col is not None:
                index_name = df.columns[index_col]
                df = df.set_index(index_name)
            return df.reset_index()
        except gspread.exceptions.WorksheetNotFound:
            print(f"Error: Worksheet '{worksheet_name}' not found.")
            return pd.DataFrame()