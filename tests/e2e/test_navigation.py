"""E2E tests for navigation between pages."""

import json
import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


class TestNavigation:
    """Test navigation between pages after onboarding completion."""

    @pytest.fixture(autouse=True)
    def setup_user(self, page: Page, sample_credentials: dict, sample_sheet_url: str):
        """Complete onboarding before each test."""
        # Mock API calls
        page.route(
            "**/oauth2.googleapis.com/**", lambda route: route.fulfill(status=200, body="{}")
        )
        page.route(
            "**/sheets.googleapis.com/**", lambda route: route.fulfill(status=200, body="{}")
        )

        # Complete onboarding
        page.goto("/onboarding")
        page.locator('button:has-text("Get Started")').click()
        page.locator('button:has-text("Next")').click()
        page.locator("textarea").fill(json.dumps(sample_credentials))
        page.locator('input[placeholder*="spreadsheets"]').fill(sample_sheet_url)
        page.locator('button:has-text("Save & Test Configuration")').click()
        page.wait_for_url(re.compile(r".*/home$|.*/$"), timeout=10000)

        # Wait for storage to sync
        page.wait_for_timeout(1000)

    def test_navigate_to_home_from_header(self, page: Page):
        """Test clicking on Kanso logo navigates to home."""
        # Start on settings page
        page.goto("/settings")
        expect(page).to_have_url(re.compile(r".*/settings$"))

        # Click on Kanso logo in header
        logo = page.locator('header a[href="/home"]').first
        expect(logo).to_be_visible()
        logo.click()

        # Should navigate to home
        expect(page).to_have_url(re.compile(r".*/home$"))

    def test_navigate_to_settings_from_header(self, page: Page):
        """Test clicking on Settings link navigates to settings."""
        page.goto("/home")

        # Click on Settings link in header
        settings_link = page.locator('header a[href="/settings"]').first
        expect(settings_link).to_be_visible()
        settings_link.click()

        # Should navigate to settings
        expect(page).to_have_url(re.compile(r".*/settings$"))

    def test_navigate_to_net_worth(self, page: Page):
        """Test navigating to Net Worth page."""
        page.goto("/home")

        # Click on Net Worth link in header
        net_worth_link = page.locator('header a[href="/net-worth"]').first
        expect(net_worth_link).to_be_visible()
        net_worth_link.click()

        # Should navigate to net-worth
        expect(page).to_have_url(re.compile(r".*/net-worth$"))

    def test_navigate_to_expenses(self, page: Page):
        """Test navigating to Expenses page."""
        page.goto("/home")

        # Click on Expenses link in header
        expenses_link = page.locator('header a[href="/expenses"]').first
        expect(expenses_link).to_be_visible()
        expenses_link.click()

        # Should navigate to expenses
        expect(page).to_have_url(re.compile(r".*/expenses$"))

    def test_navigate_to_insights(self, page: Page):
        """Test navigating to Insights page."""
        page.goto("/home")

        # Click on Insights link in header
        insights_link = page.locator('header a[href="/insights"]').first
        expect(insights_link).to_be_visible()
        insights_link.click()

        # Should navigate to insights
        expect(page).to_have_url(re.compile(r".*/insights$"))

    def test_navigate_to_quick_add(self, page: Page):
        """Test navigating to Quick Add page."""
        page.goto("/home")

        # Click on Add button in header
        add_link = page.locator('header a[href="/quick-add"]').first
        expect(add_link).to_be_visible()
        add_link.click()

        # Should navigate to quick-add
        expect(page).to_have_url(re.compile(r".*/quick-add$"))

        # Should show Add Expense title
        expect(page.locator("text=Add Expense")).to_be_visible()

    def test_quick_add_cancel_navigates_back(self, page: Page):
        """Test that Cancel button on Quick Add navigates back."""
        # Start on home, go to quick add
        page.goto("/home")
        page.locator('header a[href="/quick-add"]').first.click()
        expect(page).to_have_url(re.compile(r".*/quick-add$"))

        # Click Cancel
        cancel_button = page.locator('button:has-text("Cancel")')
        expect(cancel_button).to_be_visible()
        cancel_button.click()

        # Should navigate back to home
        expect(page).to_have_url(re.compile(r".*/home$|.*/$"), timeout=3000)

    def test_logout_redirects_to_onboarding(self, page: Page):
        """Test that logout clears state and redirects."""
        page.goto("/settings")

        # Click on Account tab (should be visible by default)
        # Logout button is in Account tab

        # Click logout button
        logout_button = page.locator('button:has-text("Logout")')
        expect(logout_button).to_be_visible()
        logout_button.click()

        # Should redirect to onboarding (logout page redirects there)
        expect(page).to_have_url(re.compile(r".*/onboarding$|.*/logout$"), timeout=5000)


class TestPageLoadsWithoutCrash:
    """Test that all pages load without crashing."""

    @pytest.fixture(autouse=True)
    def setup_user_with_mock_data(
        self, page: Page, sample_credentials: dict, sample_sheet_url: str
    ):
        """Complete onboarding and inject mock data."""
        # Mock API calls
        page.route(
            "**/oauth2.googleapis.com/**", lambda route: route.fulfill(status=200, body="{}")
        )
        page.route(
            "**/sheets.googleapis.com/**", lambda route: route.fulfill(status=200, body="{}")
        )

        # Complete onboarding
        page.goto("/onboarding")
        page.locator('button:has-text("Get Started")').click()
        page.locator('button:has-text("Next")').click()
        page.locator("textarea").fill(json.dumps(sample_credentials))
        page.locator('input[placeholder*="spreadsheets"]').fill(sample_sheet_url)
        page.locator('button:has-text("Save & Test Configuration")').click()
        page.wait_for_url(re.compile(r".*/home$|.*/$"), timeout=10000)

        # Inject mock data
        mock_data_script = """
        const mockAssetsSheet = JSON.stringify({
            "columns": ["Date", "Cash", "Stocks"],
            "index": [0, 1],
            "data": [["2024-01", "€ 10.000", "€ 50.000"], ["2024-02", "€ 11.000", "€ 52.000"]]
        });
        const mockLiabilitiesSheet = JSON.stringify({
            "columns": ["Date", "Mortgage"],
            "index": [0, 1],
            "data": [["2024-01", "€ 100.000"], ["2024-02", "€ 99.500"]]
        });
        const mockExpensesSheet = JSON.stringify({
            "columns": ["Date", "Merchant", "Amount", "Category", "Type"],
            "index": [0, 1],
            "data": [
                ["2024-01", "Store A", "€ 500", "Food", "Variable"],
                ["2024-02", "Store B", "€ 600", "Food", "Variable"]
            ]
        });
        const mockIncomesSheet = JSON.stringify({
            "columns": ["Date", "Salary"],
            "index": [0, 1],
            "data": [["2024-01", "€ 3.000"], ["2024-02", "€ 3.000"]]
        });
        if (window.app && window.app.storage && window.app.storage.general) {
            window.app.storage.general.assets_sheet = mockAssetsSheet;
            window.app.storage.general.liabilities_sheet = mockLiabilitiesSheet;
            window.app.storage.general.expenses_sheet = mockExpensesSheet;
            window.app.storage.general.incomes_sheet = mockIncomesSheet;
        }
        """
        page.evaluate(mock_data_script)
        page.wait_for_timeout(500)

    def test_net_worth_page_loads(self, page: Page):
        """Test that Net Worth page loads without crashing."""
        page.goto("/net-worth")
        expect(page).to_have_url(re.compile(r".*/net-worth$"))

        # Wait for content to render
        page.wait_for_timeout(2000)

        # Page should not show error messages
        error_messages = page.locator("text=/Error|Failed|crashed/i")
        assert error_messages.count() == 0

    def test_expenses_page_loads(self, page: Page):
        """Test that Expenses page loads without crashing."""
        page.goto("/expenses")
        expect(page).to_have_url(re.compile(r".*/expenses$"))

        # Wait for content to render
        page.wait_for_timeout(2000)

        # Page should not show error messages
        error_messages = page.locator("text=/Error|Failed|crashed/i")
        assert error_messages.count() == 0

    def test_insights_page_loads(self, page: Page):
        """Test that Insights page loads without crashing."""
        page.goto("/insights")
        expect(page).to_have_url(re.compile(r".*/insights$"))

        # Wait for content to render
        page.wait_for_timeout(2000)

        # Page should not show error messages
        error_messages = page.locator("text=/Error|Failed|crashed/i")
        assert error_messages.count() == 0

    def test_quick_add_page_loads(self, page: Page):
        """Test that Quick Add page loads without crashing."""
        page.goto("/quick-add")
        expect(page).to_have_url(re.compile(r".*/quick-add$"))

        # Wait for content to render
        page.wait_for_timeout(2000)

        # Page should show Add Expense
        expect(page.locator("text=Add Expense")).to_be_visible()

        # Page should not show error messages
        error_messages = page.locator("text=/Error|Failed|crashed/i")
        assert error_messages.count() == 0
