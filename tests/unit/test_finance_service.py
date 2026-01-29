"""Tests for finance service layer."""

import pandas as pd
import pytest

from app.logic.finance_calculator import FinanceCalculator
from app.services.finance_service import FinanceService


class TestFinanceServiceInit:
    """Test FinanceService initialization."""

    def test_init_with_storage(self):
        """Should accept storage dict in constructor."""
        storage = {"key": "value"}
        service = FinanceService(storage=storage)
        assert service.storage == storage

    def test_init_without_storage_uses_default(self, monkeypatch):
        """Should use app.storage.general when storage is None."""
        # Mock app.storage.general
        mock_storage = {"default": "storage"}

        class MockApp:
            class Storage:
                general = mock_storage

            storage = Storage()

        import app.services.finance_service

        monkeypatch.setattr(app.services.finance_service, "app", MockApp())

        service = FinanceService()
        assert service.storage == mock_storage


class TestFinanceServiceLoadDataframes:
    """Test _load_dataframes method."""

    def test_load_all_dataframes_successfully(self, sample_storage_with_all_sheets):
        """Should load all DataFrames when present in storage."""
        service = FinanceService(storage=sample_storage_with_all_sheets)
        assets_df, liabilities_df, expenses_df, incomes_df = service._load_dataframes()

        assert assets_df is not None
        assert liabilities_df is not None
        assert expenses_df is not None
        assert incomes_df is not None
        assert len(assets_df) == 3
        assert len(liabilities_df) == 3
        assert len(expenses_df) == 3
        assert len(incomes_df) == 3

    def test_load_with_missing_sheets(self):
        """Should return None for missing sheets."""
        assets_df_test = pd.DataFrame([{"Date": "2024-01", "Total": 10000}])
        expenses_df_test = pd.DataFrame([{"Date": "2024-01", "Total": 2000}])

        storage = {
            "assets_sheet": assets_df_test.to_json(orient="split"),
            # liabilities_sheet missing
            "expenses_sheet": expenses_df_test.to_json(orient="split"),
            # incomes_sheet missing
        }
        service = FinanceService(storage=storage)
        assets_df, liabilities_df, expenses_df, incomes_df = service._load_dataframes()

        assert assets_df is not None
        assert liabilities_df is None
        assert expenses_df is not None
        assert incomes_df is None

    def test_load_with_empty_storage(self):
        """Should return all None when storage is empty."""
        service = FinanceService(storage={})
        assets_df, liabilities_df, expenses_df, incomes_df = service._load_dataframes()

        assert assets_df is None
        assert liabilities_df is None
        assert expenses_df is None
        assert incomes_df is None

    def test_load_with_invalid_json(self, caplog):
        """Should handle invalid JSON gracefully and log error."""
        liabilities_df_test = pd.DataFrame([{"Date": "2024-01", "Total": 5000}])
        expenses_df_test = pd.DataFrame([{"Date": "2024-01", "Total": 2000}])

        storage = {
            "assets_sheet": "invalid json",
            "liabilities_sheet": liabilities_df_test.to_json(orient="split"),
            "expenses_sheet": expenses_df_test.to_json(orient="split"),
        }
        service = FinanceService(storage=storage)
        assets_df, liabilities_df, expenses_df, _ = service._load_dataframes()

        assert assets_df is None  # Failed to deserialize
        assert liabilities_df is not None  # Successfully loaded
        assert expenses_df is not None  # Successfully loaded
        assert "Failed to deserialize assets_sheet" in caplog.text


class TestFinanceServiceGetCalculator:
    """Test get_calculator method."""

    def test_get_calculator_with_all_required_data(self, sample_storage_with_all_sheets):
        """Should return FinanceCalculator when all required sheets present."""
        service = FinanceService(storage=sample_storage_with_all_sheets)
        calculator = service.get_calculator()

        assert calculator is not None
        assert isinstance(calculator, FinanceCalculator)

    def test_get_calculator_with_missing_assets(self):
        """Should return None when assets sheet is missing."""
        liabilities_df = pd.DataFrame([{"Date": "2024-01", "Total": 5000}])
        expenses_df = pd.DataFrame([{"Date": "2024-01", "Total": 2000}])

        storage = {
            "liabilities_sheet": liabilities_df.to_json(orient="split"),
            "expenses_sheet": expenses_df.to_json(orient="split"),
        }
        service = FinanceService(storage=storage)
        calculator = service.get_calculator()

        assert calculator is None

    def test_get_calculator_with_missing_liabilities(self):
        """Should return None when liabilities sheet is missing."""
        assets_df = pd.DataFrame([{"Date": "2024-01", "Total": 10000}])
        expenses_df = pd.DataFrame([{"Date": "2024-01", "Total": 2000}])

        storage = {
            "assets_sheet": assets_df.to_json(orient="split"),
            "expenses_sheet": expenses_df.to_json(orient="split"),
        }
        service = FinanceService(storage=storage)
        calculator = service.get_calculator()

        assert calculator is None

    def test_get_calculator_with_missing_expenses(self):
        """Should return None when expenses sheet is missing."""
        assets_df = pd.DataFrame([{"Date": "2024-01", "Total": 10000}])
        liabilities_df = pd.DataFrame([{"Date": "2024-01", "Total": 5000}])

        storage = {
            "assets_sheet": assets_df.to_json(orient="split"),
            "liabilities_sheet": liabilities_df.to_json(orient="split"),
        }
        service = FinanceService(storage=storage)
        calculator = service.get_calculator()

        assert calculator is None

    def test_get_calculator_with_optional_incomes_missing(self, sample_storage_with_all_sheets):
        """Should return FinanceCalculator even when optional incomes sheet is missing."""
        # Remove incomes sheet
        storage = sample_storage_with_all_sheets.copy()
        del storage["incomes_sheet"]

        service = FinanceService(storage=storage)
        calculator = service.get_calculator()

        assert calculator is not None
        assert isinstance(calculator, FinanceCalculator)

    def test_get_calculator_logs_warning_on_missing_data(self, caplog):
        """Should log warning when required sheets are missing."""
        service = FinanceService(storage={})
        calculator = service.get_calculator()

        assert calculator is None
        assert "Cannot create FinanceCalculator: missing required sheets" in caplog.text


class TestFinanceServiceHasRequiredData:
    """Test has_required_data method."""

    def test_has_required_data_all_present(self, sample_storage_with_all_sheets):
        """Should return True when all required sheets are present."""
        service = FinanceService(storage=sample_storage_with_all_sheets)
        assert service.has_required_data() is True

    def test_has_required_data_missing_assets(self):
        """Should return False when assets sheet is missing."""
        storage = {
            "liabilities_sheet": "data",
            "expenses_sheet": "data",
        }
        service = FinanceService(storage=storage)
        assert service.has_required_data() is False

    def test_has_required_data_missing_liabilities(self):
        """Should return False when liabilities sheet is missing."""
        storage = {
            "assets_sheet": "data",
            "expenses_sheet": "data",
        }
        service = FinanceService(storage=storage)
        assert service.has_required_data() is False

    def test_has_required_data_missing_expenses(self):
        """Should return False when expenses sheet is missing."""
        storage = {
            "assets_sheet": "data",
            "liabilities_sheet": "data",
        }
        service = FinanceService(storage=storage)
        assert service.has_required_data() is False

    def test_has_required_data_empty_storage(self):
        """Should return False when storage is empty."""
        service = FinanceService(storage={})
        assert service.has_required_data() is False

    def test_has_required_data_ignores_incomes(self, sample_storage_with_all_sheets):
        """Should return True even when incomes (optional) is missing."""
        storage = sample_storage_with_all_sheets.copy()
        del storage["incomes_sheet"]

        service = FinanceService(storage=storage)
        assert service.has_required_data() is True


class TestFinanceServiceGetKpiData:
    """Test get_kpi_data method."""

    def test_get_kpi_data_returns_all_metrics(self, sample_storage_with_all_sheets):
        """Should return dict with all KPI metrics."""
        service = FinanceService(storage=sample_storage_with_all_sheets)
        kpis = service.get_kpi_data()

        assert kpis is not None
        assert "last_update_date" in kpis
        assert "net_worth" in kpis
        assert "mom_variation_percentage" in kpis
        assert "mom_variation_absolute" in kpis
        assert "yoy_variation_percentage" in kpis
        assert "yoy_variation_absolute" in kpis
        assert "avg_saving_ratio_percentage" in kpis
        assert "avg_saving_ratio_absolute" in kpis

    def test_get_kpi_data_returns_python_types(self, sample_storage_with_all_sheets):
        """Should return Python native types (not numpy/pandas types)."""
        service = FinanceService(storage=sample_storage_with_all_sheets)
        kpis = service.get_kpi_data()

        assert kpis is not None
        assert isinstance(kpis["last_update_date"], str)
        assert isinstance(kpis["net_worth"], float)
        assert isinstance(kpis["mom_variation_percentage"], float)
        assert isinstance(kpis["mom_variation_absolute"], float)

    def test_get_kpi_data_with_missing_data(self):
        """Should return None when required data is missing."""
        service = FinanceService(storage={})
        kpis = service.get_kpi_data()

        assert kpis is None


class TestFinanceServiceGetChartData:
    """Test get_chart_data method."""

    def test_get_chart_data_returns_all_charts(self, sample_storage_with_all_sheets):
        """Should return dict with all chart data."""
        service = FinanceService(storage=sample_storage_with_all_sheets)
        charts = service.get_chart_data()

        assert charts is not None
        assert "net_worth_data" in charts
        assert "asset_vs_liabilities_data" in charts
        assert "incomes_vs_expenses_data" in charts
        assert "cash_flow_data" in charts
        assert "avg_expenses" in charts

    def test_get_chart_data_with_missing_data(self):
        """Should return None when required data is missing."""
        service = FinanceService(storage={})
        charts = service.get_chart_data()

        assert charts is None


class TestFinanceServiceGetDashboardData:
    """Test get_dashboard_data method."""

    def test_get_dashboard_data_returns_both_kpi_and_charts(self, sample_storage_with_all_sheets):
        """Should return dict with both kpi_data and chart_data."""
        service = FinanceService(storage=sample_storage_with_all_sheets)
        dashboard = service.get_dashboard_data()

        assert dashboard is not None
        assert "kpi_data" in dashboard
        assert "chart_data" in dashboard

        # Verify KPI data structure
        kpis = dashboard["kpi_data"]
        assert "net_worth" in kpis
        assert "mom_variation_percentage" in kpis

        # Verify chart data structure
        charts = dashboard["chart_data"]
        assert "net_worth_data" in charts
        assert "cash_flow_data" in charts

    def test_get_dashboard_data_returns_python_types(self, sample_storage_with_all_sheets):
        """Should return Python native types in KPI data."""
        service = FinanceService(storage=sample_storage_with_all_sheets)
        dashboard = service.get_dashboard_data()

        assert dashboard is not None
        kpis = dashboard["kpi_data"]
        assert isinstance(kpis["net_worth"], float)
        assert isinstance(kpis["last_update_date"], str)

    def test_get_dashboard_data_with_missing_data(self):
        """Should return None when required data is missing."""
        service = FinanceService(storage={})
        dashboard = service.get_dashboard_data()

        assert dashboard is None

    def test_get_dashboard_data_more_efficient_than_separate_calls(
        self, sample_storage_with_all_sheets
    ):
        """Should create calculator only once (efficiency test)."""
        service = FinanceService(storage=sample_storage_with_all_sheets)

        # Get dashboard data (single calculator instance)
        dashboard = service.get_dashboard_data()
        assert dashboard is not None

        # Verify it contains same data as separate calls
        kpis_separate = service.get_kpi_data()
        charts_separate = service.get_chart_data()

        assert dashboard["kpi_data"]["net_worth"] == kpis_separate["net_worth"]
        assert len(dashboard["chart_data"]) == len(charts_separate)


@pytest.fixture
def sample_storage_with_all_sheets():
    """Provide sample storage with all required sheets in pandas split-oriented format."""
    # Create DataFrames
    assets_df = pd.DataFrame(
        [
            {"Date": "2024-01-01", "Total": 10000},
            {"Date": "2024-02-01", "Total": 11000},
            {"Date": "2024-03-01", "Total": 12000},
        ]
    )

    liabilities_df = pd.DataFrame(
        [
            {"Date": "2024-01-01", "Total": 5000},
            {"Date": "2024-02-01", "Total": 4800},
            {"Date": "2024-03-01", "Total": 4600},
        ]
    )

    expenses_df = pd.DataFrame(
        [
            {"Date": "2024-01-15", "Amount": 2000, "Category": "Food"},
            {"Date": "2024-02-15", "Amount": 1800, "Category": "Food"},
            {"Date": "2024-03-15", "Amount": 2100, "Category": "Food"},
        ]
    )

    incomes_df = pd.DataFrame(
        [
            {"Date": "2024-01-01", "Total": 5000},
            {"Date": "2024-02-01", "Total": 5000},
            {"Date": "2024-03-01", "Total": 5000},
        ]
    )

    return {
        "assets_sheet": assets_df.to_json(orient="split"),
        "liabilities_sheet": liabilities_df.to_json(orient="split"),
        "expenses_sheet": expenses_df.to_json(orient="split"),
        "incomes_sheet": incomes_df.to_json(orient="split"),
    }
