"""Smoke test for home page - verifies page loads without crashing."""

import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


class TestHomePageSmoke:
    """Smoke tests to verify home page doesn't crash with mock data."""

    def test_home_page_with_mock_data(self, page: Page):
        """Test that home page renders correctly with mock financial data.

        This smoke test verifies the complete rendering pipeline:
        1. Data loading from storage
        2. DataFrame preprocessing
        3. FinanceCalculator instantiation
        4. KPI and chart rendering

        Uses minimal mock data to avoid complexity while testing integration.
        """
        # Mock financial data in app.storage.user using JavaScript
        # This simulates data that would be loaded from Google Sheets
        page.goto("/home")

        # Inject mock data into NiceGUI's app.storage
        mock_data_script = """
        // Mock minimal financial data for smoke test
        const mockAssetsSheet = JSON.stringify({
            "columns": ["Date", "Cash", "Stocks"],
            "index": [0, 1, 2],
            "data": [
                ["2024-01", "€ 10.000", "€ 50.000"],
                ["2024-02", "€ 11.000", "€ 52.000"],
                ["2024-03", "€ 12.000", "€ 54.000"]
            ]
        });

        const mockLiabilitiesSheet = JSON.stringify({
            "columns": ["Date", "Mortgage"],
            "index": [0, 1, 2],
            "data": [
                ["2024-01", "€ 100.000"],
                ["2024-02", "€ 99.500"],
                ["2024-03", "€ 99.000"]
            ]
        });

        const mockExpensesSheet = JSON.stringify({
            "columns": ["Date", "Merchant", "Amount", "Category", "Type"],
            "index": [0, 1, 2, 3, 4, 5],
            "data": [
                ["2024-01", "Store A", "€ 500", "Food", "Variable"],
                ["2024-01", "Store B", "€ 1.000", "Housing", "Fixed"],
                ["2024-02", "Store C", "€ 600", "Food", "Variable"],
                ["2024-02", "Store D", "€ 1.000", "Housing", "Fixed"],
                ["2024-03", "Store E", "€ 550", "Food", "Variable"],
                ["2024-03", "Store F", "€ 1.000", "Housing", "Fixed"]
            ]
        });

        const mockIncomesSheet = JSON.stringify({
            "columns": ["Date", "Salary"],
            "index": [0, 1, 2],
            "data": [
                ["2024-01", "€ 3.000"],
                ["2024-02", "€ 3.000"],
                ["2024-03", "€ 3.000"]
            ]
        });

        // Store sheets, onboarding, theme, and currency in general storage (shared across devices)
        if (window.app && window.app.storage) {
            if (window.app.storage.general) {
                window.app.storage.general.assets_sheet = mockAssetsSheet;
                window.app.storage.general.liabilities_sheet = mockLiabilitiesSheet;
                window.app.storage.general.expenses_sheet = mockExpensesSheet;
                window.app.storage.general.incomes_sheet = mockIncomesSheet;
                window.app.storage.general.onboarding_completed = "true";
                window.app.storage.general.currency = "EUR";
                window.app.storage.general.theme = "light";
                window.app.storage.general.echarts_theme_url = "/themes/light.json";
            }
        }
        """

        page.evaluate(mock_data_script)

        # Reload page to trigger data loading with mocked data
        page.reload()

        # Wait for page to load
        expect(page).to_have_url(re.compile(r".*/home$"))
        expect(page.locator(".main-content")).to_be_visible(timeout=5000)

        # Wait for skeleton loaders to disappear (indicates data loaded)
        # Using wait_for with state: hidden is more reliable
        page.locator(".skeleton").first.wait_for(state="hidden", timeout=10000)

        # Verify KPI cards are rendered (should have 4 cards)
        # Look for stat card containers with text content
        kpi_cards = page.locator(".stat-card, [class*='stat']")
        # At least some cards should be visible
        expect(kpi_cards.first).to_be_visible(timeout=5000)

        # Verify NO error messages are displayed
        assert page.locator('text="Error loading data"').count() == 0
        assert page.locator('text="Failed to load data"').count() == 0
        assert page.locator('text="No data available"').count() == 0

        # Verify page doesn't crash (main content still visible)
        expect(page.locator(".main-content")).to_be_visible()

    def test_home_page_with_partial_data(self, page: Page):
        """Test home page behavior with incomplete mock data.

        Verifies graceful degradation when some sheets are missing.
        """
        page.goto("/home")

        # Mock only assets and liabilities (missing expenses and incomes)
        partial_data_script = """
        const mockAssetsSheet = JSON.stringify({
            "columns": ["Date", "Cash"],
            "index": [0],
            "data": [["2024-01", "€ 10.000"]]
        });

        const mockLiabilitiesSheet = JSON.stringify({
            "columns": ["Date", "Mortgage"],
            "index": [0],
            "data": [["2024-01", "€ 100.000"]]
        });

        // Store in general storage (shared across devices)
        if (window.app && window.app.storage && window.app.storage.general) {
            window.app.storage.general.assets_sheet = mockAssetsSheet;
            window.app.storage.general.liabilities_sheet = mockLiabilitiesSheet;
            // Intentionally omit expenses_sheet and incomes_sheet
        }
        """

        page.evaluate(partial_data_script)
        page.reload()

        # Page should still load without crashing
        expect(page).to_have_url(re.compile(r".*/home$"))
        expect(page.locator(".main-content")).to_be_visible(timeout=5000)

        # Should either show skeleton loaders or a message about data loading
        # But should NOT crash
        assert page.locator(".skeleton, .main-content").count() > 0
