"""Google Sheets API service.

This module provides a service class for interacting with Google Sheets,
including authentication, data fetching, and optional validation.

Key features:
    - Service account authentication
    - DataFrame conversion with single or MultiIndex support
    - Optional Pydantic validation for data quality
    - Non-blocking validation (logs warnings but allows data loading)

Example:
    >>> from app.services.google_sheets import GoogleSheetService
    >>> service = GoogleSheetService('credentials.json', 'https://docs.google.com/...')
    >>> df = service.get_worksheet_as_dataframe('Data', header=0)
"""

import logging
from pathlib import Path

import gspread
import pandas as pd

from app.core.monitoring import track_performance
from app.core.validators import DataSheetRow, ExpenseRow, validate_dataframe_structure

logger = logging.getLogger(__name__)


class GoogleSheetService:
    """Service class for interacting with Google Sheets API.

    Handles authentication, workbook access, and worksheet data fetching
    with automatic conversion to pandas DataFrames.

    Attributes:
        creds_path: Path to service account credentials JSON file
        workbook_url: URL of the Google Sheets workbook
        client: Authenticated gspread client

    Example:
        >>> service = GoogleSheetService(
        ...     credentials_path='config/credentials/service_account.json',
        ...     workbook_url='https://docs.google.com/spreadsheets/d/...'
        ... )
        >>> df = service.get_worksheet_as_dataframe('Data')
    """

    def __init__(self, credentials_path: str | Path, workbook_url: str) -> None:
        """Initialize the Google Sheets service.

        Args:
            credentials_path: Path to Google service account credentials JSON file
            workbook_url: Full URL of the Google Sheets workbook

        Raises:
            FileNotFoundError: If credentials file doesn't exist at the specified path
        """
        self.creds_path = Path(credentials_path)
        self.workbook_url = workbook_url
        if not self.creds_path.exists():
            raise FileNotFoundError(f"Credentials file not found at: {self.creds_path}")
        self.client = self._authenticate()
        logger.info(f"Google Sheets service initialized for workbook: {workbook_url}")

    def _authenticate(self) -> gspread.Client:
        """Authenticate with Google Sheets using service account credentials.

        Returns:
            Authenticated gspread Client instance
        """
        return gspread.service_account(filename=str(self.creds_path))

    @track_performance("google_sheets_fetch")
    def get_worksheet_as_dataframe(
        self,
        worksheet_name: str,
        header: int | list[int] = 0,
        index_col: int | None = 0,
        validate: bool = True,
    ) -> pd.DataFrame:
        """Get worksheet data as a pandas DataFrame with optional validation.

        Fetches all data from the specified worksheet and converts it to a DataFrame.
        Supports both single-level and MultiIndex column headers. Optionally validates
        data structure using Pydantic models (non-blocking).

        Args:
            worksheet_name: Name of the worksheet to fetch (e.g., "Data", "Expenses")
            header: Row index or list of indices to use as column names.
                   Use [0, 1] for two-level MultiIndex headers.
            index_col: Column index to use as DataFrame index, or None for default index
            validate: If True, validates data structure and logs warnings for issues.
                     Validation is non-blocking and won't prevent data loading.

        Returns:
            DataFrame containing the worksheet data, or empty DataFrame if worksheet
            not found

        Example:
            >>> # Single header row
            >>> df = service.get_worksheet_as_dataframe('Data', header=0)
            >>> # Two-level MultiIndex header
            >>> df = service.get_worksheet_as_dataframe('Assets', header=[0, 1])

        Note:
            MultiIndex columns are automatically sorted to avoid pandas performance warnings.
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
        """Validate worksheet data structure (non-blocking).

        Uses Pydantic models to validate data format and structure. Logs warnings
        for validation errors but doesn't raise exceptions, allowing the application
        to gracefully handle imperfect data.

        Args:
            worksheet_name: Name of worksheet being validated (used to select validator)
            df: DataFrame to validate

        Note:
            - Automatically selects DataSheetRow validator for "data" worksheets
            - Automatically selects ExpenseRow validator for "expense" worksheets
            - Logs only first 3 errors as examples to avoid log spam
            - Validation is skipped for worksheets with MultiIndex columns
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
