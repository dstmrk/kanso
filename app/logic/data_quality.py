"""Data quality checker for validating completeness of financial data.

This module provides quality checks for detecting:
    - Missing sheets (sheets not loaded from Google Sheets)
    - Empty sheets (sheets with 0 data rows)
    - Missing required columns (Date column for all sheets, specific columns for Expenses)

The checks are designed to provide actionable warnings to users about their data.
"""

import logging
from dataclasses import dataclass
from io import StringIO
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class DataQualityWarning:
    """Represents a data quality issue.

    Attributes:
        sheet_name: Name of the sheet with the issue (e.g., "Assets", "Expenses")
        severity: Warning level - "error" or "warning"
        message: Human-readable description of the issue
        details: Optional additional context
    """

    sheet_name: str
    severity: str  # "error" or "warning"
    message: str
    details: str | None = None


class DataQualityChecker:
    """Checks data quality for all financial sheets.

    This class provides methods to validate that all required sheets are present,
    contain data, and have the necessary columns.

    Example:
        >>> checker = DataQualityChecker()
        >>> warnings = checker.check_all(storage)
        >>> for warning in warnings:
        ...     print(f"{warning.severity.upper()}: {warning.sheet_name} - {warning.message}")
    """

    REQUIRED_SHEETS = ["assets_sheet", "liabilities_sheet", "incomes_sheet", "expenses_sheet"]
    SHEET_DISPLAY_NAMES = {
        "assets_sheet": "Assets",
        "liabilities_sheet": "Liabilities",
        "incomes_sheet": "Incomes",
        "expenses_sheet": "Expenses",
    }

    # Required columns for each sheet
    REQUIRED_COLUMNS = {
        "assets_sheet": ["Date"],
        "liabilities_sheet": ["Date"],
        "incomes_sheet": ["Date"],
        "expenses_sheet": ["Date", "Merchant", "Amount", "Category", "Type"],
    }

    def check_missing_sheets(self, storage: dict[str, Any]) -> list[DataQualityWarning]:
        """Check if any required sheets are missing from storage.

        Args:
            storage: The app storage dictionary containing sheet data

        Returns:
            List of warnings for missing sheets
        """
        warnings = []

        for sheet_key in self.REQUIRED_SHEETS:
            if sheet_key not in storage or not storage[sheet_key]:
                display_name = self.SHEET_DISPLAY_NAMES[sheet_key]
                warnings.append(
                    DataQualityWarning(
                        sheet_name=display_name,
                        severity="error",
                        message=f"{display_name} sheet is not loaded",
                        details="Please check your Google Sheets configuration and refresh data.",
                    )
                )
                logger.warning(f"Missing sheet: {display_name}")

        return warnings

    def check_empty_sheets(self, storage: dict[str, Any]) -> list[DataQualityWarning]:
        """Check if any sheets have zero data rows.

        Args:
            storage: The app storage dictionary containing sheet data

        Returns:
            List of warnings for empty sheets
        """
        warnings = []

        for sheet_key in self.REQUIRED_SHEETS:
            # Skip if sheet is missing (already caught by check_missing_sheets)
            if sheet_key not in storage or not storage[sheet_key]:
                continue

            try:
                df = pd.read_json(StringIO(storage[sheet_key]), orient="split")

                if df.empty or len(df) == 0:
                    display_name = self.SHEET_DISPLAY_NAMES[sheet_key]
                    warnings.append(
                        DataQualityWarning(
                            sheet_name=display_name,
                            severity="warning",
                            message=f"{display_name} sheet has no data",
                            details="Add at least one row of data to see visualizations.",
                        )
                    )
                    logger.warning(f"Empty sheet: {display_name}")

            except (ValueError, TypeError) as e:
                display_name = self.SHEET_DISPLAY_NAMES[sheet_key]
                logger.error(f"Error checking {display_name} sheet: {e}")
                warnings.append(
                    DataQualityWarning(
                        sheet_name=display_name,
                        severity="error",
                        message=f"Failed to read {display_name} sheet",
                        details=str(e),
                    )
                )

        return warnings

    @staticmethod
    def _extract_column_names(df: pd.DataFrame) -> list[Any]:
        """Extract top-level column names, handling both MultiIndex and single-level columns."""
        if isinstance(df.columns, pd.MultiIndex):
            return df.columns.get_level_values(0).tolist()
        return [col[0] if isinstance(col, tuple) and len(col) > 0 else col for col in df.columns]

    def _check_columns_for_sheet(
        self, sheet_key: str, df: pd.DataFrame
    ) -> DataQualityWarning | None:
        """Check a single sheet for missing required columns. Returns a warning or None."""
        column_names = self._extract_column_names(df)
        required_cols = self.REQUIRED_COLUMNS[sheet_key]
        missing_cols = [col for col in required_cols if col not in column_names]

        if not missing_cols:
            return None

        display_name = self.SHEET_DISPLAY_NAMES[sheet_key]
        logger.warning(f"Missing columns in {display_name}: {missing_cols}")
        return DataQualityWarning(
            sheet_name=display_name,
            severity="error",
            message=f"{display_name} sheet is missing required columns",
            details=f"Missing: {', '.join(missing_cols)}",
        )

    def check_missing_columns(self, storage: dict[str, Any]) -> list[DataQualityWarning]:
        """Check if any sheets are missing required columns.

        Args:
            storage: The app storage dictionary containing sheet data

        Returns:
            List of warnings for missing required columns
        """
        warnings = []

        for sheet_key in self.REQUIRED_SHEETS:
            if sheet_key not in storage or not storage[sheet_key]:
                continue

            try:
                df = pd.read_json(StringIO(storage[sheet_key]), orient="split")
                if df.empty or len(df) == 0:
                    continue

                warning = self._check_columns_for_sheet(sheet_key, df)
                if warning:
                    warnings.append(warning)

            except (ValueError, TypeError, KeyError) as e:
                display_name = self.SHEET_DISPLAY_NAMES[sheet_key]
                logger.error(f"Error checking columns in {display_name} sheet: {e}")
                warnings.append(
                    DataQualityWarning(
                        sheet_name=display_name,
                        severity="error",
                        message=f"Failed to check columns in {display_name} sheet",
                        details=str(e),
                    )
                )

        return warnings

    def check_all(self, storage: dict[str, Any]) -> list[DataQualityWarning]:
        """Run all data quality checks.

        Args:
            storage: The app storage dictionary containing sheet data

        Returns:
            Combined list of all warnings from all checks

        Example:
            >>> checker = DataQualityChecker()
            >>> warnings = checker.check_all(storage)
            >>> if warnings:
            ...     print(f"Found {len(warnings)} data quality issues")
            >>> else:
            ...     print("All data quality checks passed")
        """
        all_warnings = []

        # Check in order of severity
        all_warnings.extend(self.check_missing_sheets(storage))
        all_warnings.extend(self.check_empty_sheets(storage))
        all_warnings.extend(self.check_missing_columns(storage))

        if all_warnings:
            logger.info(f"Data quality check found {len(all_warnings)} issue(s)")
        else:
            logger.info("Data quality check passed - no issues found")

        return all_warnings
