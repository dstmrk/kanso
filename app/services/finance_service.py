"""Finance service layer for managing financial calculations and data access.

This service provides a clean abstraction layer between UI components and the
FinanceCalculator business logic. It handles:
    - Data loading from storage
    - JSON deserialization with error handling
    - FinanceCalculator instantiation and caching
    - High-level methods for common financial metrics

This decouples UI components from direct FinanceCalculator usage and centralizes
data access logic.
"""

import logging
from typing import Any

import pandas as pd
from nicegui import app

from app.logic.finance_calculator import FinanceCalculator
from app.services import utils

logger = logging.getLogger(__name__)


class FinanceService:
    """Service for financial calculations with centralized data management.

    Provides high-level methods for UI components to access financial data
    without directly managing DataFrame loading or FinanceCalculator instantiation.

    Example:
        >>> service = FinanceService()
        >>> calculator = await service.get_calculator()
        >>> net_worth = calculator.get_current_net_worth()
    """

    def __init__(self, storage: dict[str, Any] | None = None):
        """Initialize FinanceService.

        Args:
            storage: Optional storage dictionary. If None, uses app.storage.general
        """
        self.storage = storage if storage is not None else app.storage.general

    def _load_dataframes(self) -> tuple[pd.DataFrame | None, ...]:
        """Load all financial DataFrames from storage with error handling.

        Returns:
            Tuple of (assets_df, liabilities_df, expenses_df, incomes_df)
            Any DataFrame can be None if not available or if deserialization fails

        Note:
            Errors during JSON deserialization are logged but don't raise exceptions,
            allowing graceful degradation when some sheets are invalid.
        """
        assets_df = None
        liabilities_df = None
        expenses_df = None
        incomes_df = None

        # Load Assets
        assets_sheet_str = self.storage.get("assets_sheet")
        if assets_sheet_str:
            try:
                assets_df = utils.read_json(assets_sheet_str)
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to deserialize assets_sheet: {e}")

        # Load Liabilities
        liabilities_sheet_str = self.storage.get("liabilities_sheet")
        if liabilities_sheet_str:
            try:
                liabilities_df = utils.read_json(liabilities_sheet_str)
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to deserialize liabilities_sheet: {e}")

        # Load Expenses
        expenses_sheet_str = self.storage.get("expenses_sheet")
        if expenses_sheet_str:
            try:
                expenses_df = utils.read_json(expenses_sheet_str)
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to deserialize expenses_sheet: {e}")

        # Load Incomes (optional)
        incomes_sheet_str = self.storage.get("incomes_sheet")
        if incomes_sheet_str:
            try:
                incomes_df = utils.read_json(incomes_sheet_str)
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to deserialize incomes_sheet: {e}")

        return assets_df, liabilities_df, expenses_df, incomes_df

    def get_calculator(self) -> FinanceCalculator | None:
        """Get FinanceCalculator instance with loaded data.

        Loads all financial DataFrames from storage and creates a FinanceCalculator
        instance. Returns None if required sheets (assets, liabilities, expenses)
        are not available.

        Returns:
            FinanceCalculator instance if data is available, None otherwise

        Example:
            >>> service = FinanceService()
            >>> calculator = service.get_calculator()
            >>> if calculator:
            ...     net_worth = calculator.get_current_net_worth()
        """
        assets_df, liabilities_df, expenses_df, incomes_df = self._load_dataframes()

        # Check if required sheets are available
        if assets_df is None or liabilities_df is None or expenses_df is None:
            logger.warning("Cannot create FinanceCalculator: missing required sheets")
            return None

        return FinanceCalculator(
            assets_df=assets_df,
            liabilities_df=liabilities_df,
            expenses_df=expenses_df,
            incomes_df=incomes_df,
        )

    def has_required_data(self) -> bool:
        """Check if all required financial data is available in storage.

        Returns:
            True if assets, liabilities, and expenses sheets are all present
        """
        return all(
            self.storage.get(key) for key in ["assets_sheet", "liabilities_sheet", "expenses_sheet"]
        )

    def get_kpi_data(self) -> dict[str, Any] | None:
        """Get all key performance indicators in a single dict.

        Loads calculator and computes all KPIs at once. Returns None if data
        is not available.

        Returns:
            Dictionary containing:
                - last_update_date: str
                - net_worth: float
                - mom_variation_percentage: float
                - mom_variation_absolute: float
                - yoy_variation_percentage: float
                - yoy_variation_absolute: float
                - avg_saving_ratio_percentage: float
                - avg_saving_ratio_absolute: float

        Example:
            >>> service = FinanceService()
            >>> kpis = service.get_kpi_data()
            >>> if kpis:
            ...     print(f"Net Worth: {kpis['net_worth']}")
        """
        calculator = self.get_calculator()
        if not calculator:
            return None

        # Ensure all values are Python native types (not numpy/pandas types)
        return {
            "last_update_date": str(calculator.get_last_update_date()),
            "net_worth": float(calculator.get_current_net_worth()),
            "mom_variation_percentage": float(
                calculator.get_month_over_month_net_worth_variation_percentage()
            ),
            "mom_variation_absolute": float(
                calculator.get_month_over_month_net_worth_variation_absolute()
            ),
            "yoy_variation_percentage": float(
                calculator.get_year_over_year_net_worth_variation_percentage()
            ),
            "yoy_variation_absolute": float(
                calculator.get_year_over_year_net_worth_variation_absolute()
            ),
            "avg_saving_ratio_percentage": float(
                calculator.get_average_saving_ratio_last_12_months_percentage()
            ),
            "avg_saving_ratio_absolute": float(
                calculator.get_average_saving_ratio_last_12_months_absolute()
            ),
        }

    def get_chart_data(self) -> dict[str, Any] | None:
        """Get all chart data for dashboard visualizations.

        Loads calculator and retrieves data for all dashboard charts at once.
        Returns None if data is not available.

        Returns:
            Dictionary containing:
                - net_worth_data: Monthly net worth data
                - asset_vs_liabilities_data: Assets vs liabilities breakdown
                - incomes_vs_expenses_data: Income vs expense comparison
                - cash_flow_data: Last 12 months cash flow
                - avg_expenses: Average expenses by category (last 12 months)

        Example:
            >>> service = FinanceService()
            >>> charts = service.get_chart_data()
            >>> if charts:
            ...     net_worth_series = charts['net_worth_data']
        """
        calculator = self.get_calculator()
        if not calculator:
            return None

        return {
            "net_worth_data": calculator.get_monthly_net_worth(),
            "asset_vs_liabilities_data": calculator.get_assets_liabilities(),
            "incomes_vs_expenses_data": calculator.get_incomes_vs_expenses(),
            "cash_flow_data": calculator.get_cash_flow_last_12_months(),
            "avg_expenses": calculator.get_average_expenses_by_category_last_12_months(),
        }

    def get_dashboard_data(self) -> dict[str, Any] | None:
        """Get all dashboard data (KPIs + charts) in a single call.

        This is more efficient than calling get_kpi_data() and get_chart_data()
        separately, as it creates the FinanceCalculator only once and retrieves
        all data in a single pass.

        Returns:
            Dictionary containing both 'kpi_data' and 'chart_data' keys,
            or None if data is not available

        Example:
            >>> service = FinanceService()
            >>> data = service.get_dashboard_data()
            >>> if data:
            ...     print(f"Net Worth: {data['kpi_data']['net_worth']}")
            ...     print(f"Chart dates: {data['chart_data']['net_worth_data']['dates']}")
        """
        calculator = self.get_calculator()
        if not calculator:
            return None

        # Compute all KPIs and chart data with a single calculator instance
        return {
            "kpi_data": {
                "last_update_date": str(calculator.get_last_update_date()),
                "net_worth": float(calculator.get_current_net_worth()),
                "mom_variation_percentage": float(
                    calculator.get_month_over_month_net_worth_variation_percentage()
                ),
                "mom_variation_absolute": float(
                    calculator.get_month_over_month_net_worth_variation_absolute()
                ),
                "yoy_variation_percentage": float(
                    calculator.get_year_over_year_net_worth_variation_percentage()
                ),
                "yoy_variation_absolute": float(
                    calculator.get_year_over_year_net_worth_variation_absolute()
                ),
                "avg_saving_ratio_percentage": float(
                    calculator.get_average_saving_ratio_last_12_months_percentage()
                ),
                "avg_saving_ratio_absolute": float(
                    calculator.get_average_saving_ratio_last_12_months_absolute()
                ),
            },
            "chart_data": {
                "net_worth_data": calculator.get_monthly_net_worth(),
                "asset_vs_liabilities_data": calculator.get_assets_liabilities(),
                "incomes_vs_expenses_data": calculator.get_incomes_vs_expenses(),
                "cash_flow_data": calculator.get_cash_flow_last_12_months(),
                "avg_expenses": calculator.get_average_expenses_by_category_last_12_months(),
            },
        }
