import logging
from pathlib import Path

import gspread
import pandas as pd

from app.core.validators import DataSheetRow, ExpenseRow, validate_dataframe_structure

logger = logging.getLogger(__name__)


class GoogleSheetService:
    """Service class for interacting with Google Sheets API."""

    def __init__(self, credentials_path: str | Path, workbook_url: str) -> None:
        """Initialize with credentials and workbook ID."""
        self.creds_path = Path(credentials_path)
        self.workbook_url = workbook_url
        if not self.creds_path.exists():
            raise FileNotFoundError(f"Credentials file not found at: {self.creds_path}")
        self.client = self._authenticate()
        logger.info(f"Google Sheets service initialized for workbook: {workbook_url}")

    def _authenticate(self) -> gspread.Client:
        """Authenticate with Google Sheets using service account credentials."""
        return gspread.service_account(filename=str(self.creds_path))

    def get_worksheet_as_dataframe(
        self,
        worksheet_name: str,
        header: int | list[int] = 0,
        index_col: int | None = 0,
        validate: bool = True,
    ) -> pd.DataFrame:
        """
        Get worksheet data as a pandas DataFrame with optional validation.

        Args:
            worksheet_name: Name of the worksheet to fetch
            header: Row index(es) to use as column names
            index_col: Column to use as the DataFrame index
            validate: Whether to validate data structure (non-blocking)

        Returns:
            DataFrame containing the worksheet data
        """
        try:
            sheet = self.client.open_by_url(self.workbook_url).worksheet(worksheet_name)
            data = sheet.get_all_values()
            if not data:
                return pd.DataFrame()
            df = pd.DataFrame(data)

            # Handle MultiIndex columns (two-level: category and specific item)
            header_rows_to_drop: list[int]
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

            result_df = df.reset_index()

            # Optional non-blocking validation
            if validate and not isinstance(df.columns, pd.MultiIndex):
                self._validate_worksheet_data(worksheet_name, result_df)

            return result_df
        except gspread.exceptions.WorksheetNotFound:
            logger.error(f"Worksheet '{worksheet_name}' not found")
            return pd.DataFrame()

    def _validate_worksheet_data(self, worksheet_name: str, df: pd.DataFrame) -> None:
        """
        Validate worksheet data structure (non-blocking).

        Logs warnings if validation fails but doesn't prevent data loading.
        """
        # Convert DataFrame to list of dicts for validation
        data_rows = df.to_dict("records")

        # Choose appropriate validator based on worksheet name
        validator = None
        if "data" in worksheet_name.lower():
            validator = DataSheetRow
        elif "expense" in worksheet_name.lower():
            validator = ExpenseRow

        if validator:
            is_valid, errors = validate_dataframe_structure(data_rows, validator)
            if not is_valid:
                logger.warning(
                    f"Validation issues in worksheet '{worksheet_name}': {len(errors)} error(s)"
                )
                # Log first 3 errors as examples
                for error in errors[:3]:
                    logger.warning(f"  - {error}")
                if len(errors) > 3:
                    logger.warning(f"  ... and {len(errors) - 3} more error(s)")
            else:
                logger.debug(f"Worksheet '{worksheet_name}' validation passed")
