import gspread
import pandas as pd
from pathlib import Path

class GoogleSheetService:
    """Service class for interacting with Google Sheets API."""
    
    def __init__(self, credentials_path, workbook_id):
        """Initialize with credentials and workbook ID."""
        self.creds_path = Path(credentials_path)
        self.workbook_id = workbook_id
        if not self.creds_path.exists():
            raise FileNotFoundError(f"Credentials file not found at: {self.creds_path}")
        self.client = self._authenticate()

    def _authenticate(self):
        """Authenticate with Google Sheets using service account credentials."""
        return gspread.service_account(filename=str(self.creds_path))

    def get_worksheet_as_dataframe(self, worksheet_name, header=0, index_col=0):
        """Fetch worksheet data and convert to pandas DataFrame."""
        try:
            # Open worksheet and get all values
            sheet = self.client.open_by_key(self.workbook_id).worksheet(worksheet_name)
            data = sheet.get_all_values()
            if not data:
                return pd.DataFrame()
            
            # Convert to DataFrame and handle headers
            df = pd.DataFrame(data)
            # Ensure we get a Series for column names, not a DataFrame
            # Handle header row(s) - can be int or list
            if isinstance(header, int):
                df.columns = df.iloc[header]
                header_rows_to_drop = [header]
            else:
                # If header is a list, use the first row for column names
                df.columns = df.iloc[header[0]]
                header_rows_to_drop = header
            df = df.drop(header_rows_to_drop)
            
            # Set index column if specified
            if index_col is not None:
                index_name = df.columns[index_col]
                df = df.set_index(index_name)
            
            return df.reset_index()
        except gspread.exceptions.WorksheetNotFound:
            print(f"Error: Worksheet '{worksheet_name}' not found.")
            return pd.DataFrame()