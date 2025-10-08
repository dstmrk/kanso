from typing import Union, List, Optional
import gspread
import pandas as pd
from pathlib import Path

class GoogleSheetService:
    """Service class for interacting with Google Sheets API."""

    def __init__(self, credentials_path: Union[str, Path], workbook_id: str) -> None:
        """Initialize with credentials and workbook ID."""
        self.creds_path = Path(credentials_path)
        self.workbook_id = workbook_id
        if not self.creds_path.exists():
            raise FileNotFoundError(f"Credentials file not found at: {self.creds_path}")
        self.client = self._authenticate()

    def _authenticate(self) -> gspread.Client:
        """Authenticate with Google Sheets using service account credentials."""
        return gspread.service_account(filename=str(self.creds_path))

    def get_worksheet_as_dataframe(self, worksheet_name: str, header: Union[int, List[int]] = 0, index_col: Union[int, None] = 0) -> pd.DataFrame:
        try:
            sheet = self.client.open_by_key(self.workbook_id).worksheet(worksheet_name)
            data = sheet.get_all_values()
            if not data:
                return pd.DataFrame()
            df = pd.DataFrame(data)

            # Handle MultiIndex columns (two-level: category and specific item)
            header_rows_to_drop: List[int]
            if isinstance(header, list) and len(header) == 2:
                # Create MultiIndex from the two header rows
                header_data = [df.iloc[i].tolist() for i in header]
                df.columns = pd.MultiIndex.from_arrays(header_data)
                # Sort the MultiIndex to avoid performance warning
                df = df.sort_index(axis=1)
                header_rows_to_drop = header
            else:
                # Single header row
                df.columns = df.iloc[header]
                header_rows_to_drop = [header] if isinstance(header, int) else list(header)

            df = df.drop(header_rows_to_drop)

            if index_col is not None:
                index_name = df.columns[index_col]
                df = df.set_index(index_name)
            return df.reset_index()
        except gspread.exceptions.WorksheetNotFound:
            print(f"Error: Worksheet '{worksheet_name}' not found.")
            return pd.DataFrame()