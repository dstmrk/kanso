import gspread
import pandas as pd
from pathlib import Path
from typing import List, Union, Optional

class GoogleSheetService:
    def __init__(self, credentials_path: Union[str, Path], workbook_id: str) -> None:
        self.creds_path: Path = Path(credentials_path)
        self.workbook_id: str = workbook_id
        if not self.creds_path.exists():
            raise FileNotFoundError(f"Credentials file not found at: {self.creds_path}")
        self.client: gspread.Client = self._authenticate()

    def _authenticate(self) -> gspread.Client:
        return gspread.service_account(filename=str(self.creds_path))

    def get_worksheet_as_dataframe(self, worksheet_name: str, header: Union[int, List[int]] = 0, index_col: Optional[int] = 0) -> pd.DataFrame:
        try:
            sheet: gspread.Worksheet = self.client.open_by_key(self.workbook_id).worksheet(worksheet_name)
            data: List[List[str]] = sheet.get_all_values()
            if not data:
                return pd.DataFrame()
            df: pd.DataFrame = pd.DataFrame(data)
            # Ensure we get a Series for column names, not a DataFrame
            if isinstance(header, int):
                df.columns = df.iloc[header]
                header_rows_to_drop: List[int] = [header]
            else:
                # If header is a list, use the first row for column names
                df.columns = df.iloc[header[0]]
                header_rows_to_drop = header
            df = df.drop(header_rows_to_drop)
            if index_col is not None:
                index_name: str = df.columns[index_col]
                df = df.set_index(index_name)
            return df.reset_index()
        except gspread.exceptions.WorksheetNotFound:
            print(f"Error: Worksheet '{worksheet_name}' not found.")
            return pd.DataFrame()