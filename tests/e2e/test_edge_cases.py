"""E2E tests for edge cases and error handling."""

import json
import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


class TestEmptyDataHandling:
    """Test that pages handle empty or missing data gracefully."""

    @pytest.fixture(autouse=True)
    def setup_user_no_data(self, page: Page, sample_credentials: dict, sample_sheet_url: str):
        """Complete onboarding but don't inject any sheet data."""
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

    def test_home_page_with_no_data(self, page: Page):
        """Test that home page doesn't crash when there's no sheet data."""
        page.goto("/home")
        expect(page).to_have_url(re.compile(r".*/home$"))

        # Wait for page to attempt rendering
        page.wait_for_timeout(3000)

        # Page should not crash - main content should be visible
        expect(page.locator(".main-content")).to_be_visible()

    def test_net_worth_page_with_no_data(self, page: Page):
        """Test that Net Worth page handles missing data."""
        page.goto("/net-worth")
        expect(page).to_have_url(re.compile(r".*/net-worth$"))

        # Wait for page to attempt rendering
        page.wait_for_timeout(3000)

        # Page should not crash

    def test_expenses_page_with_no_data(self, page: Page):
        """Test that Expenses page handles missing data."""
        page.goto("/expenses")
        expect(page).to_have_url(re.compile(r".*/expenses$"))

        # Wait for page to attempt rendering
        page.wait_for_timeout(3000)

        # Page should not crash

    def test_quick_add_with_no_data(self, page: Page):
        """Test that Quick Add page works even without existing expenses."""
        page.goto("/quick-add")
        expect(page).to_have_url(re.compile(r".*/quick-add$"))

        # Wait for form to render
        page.wait_for_timeout(2000)

        # Add Expense title should be visible (use .first to avoid ambiguity with button)
        expect(page.get_by_text("Add Expense").first).to_be_visible()

        # Form buttons should be present
        expect(page.locator('button:has-text("Cancel")')).to_be_visible()


class TestPartialDataHandling:
    """Test that pages handle partial data gracefully."""

    @pytest.fixture(autouse=True)
    def setup_user_partial_data(self, page: Page, sample_credentials: dict, sample_sheet_url: str):
        """Complete onboarding and inject only partial data (assets only)."""
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

        # Inject only assets data (missing liabilities, expenses, incomes)
        partial_data_script = """
        const mockAssetsSheet = JSON.stringify({
            "columns": ["Date", "Cash", "Stocks"],
            "index": [0, 1],
            "data": [["2024-01", "€ 10.000", "€ 50.000"], ["2024-02", "€ 11.000", "€ 52.000"]]
        });
        if (window.app && window.app.storage && window.app.storage.general) {
            window.app.storage.general.assets_sheet = mockAssetsSheet;
            // Intentionally omit liabilities, expenses, incomes
        }
        """
        page.evaluate(partial_data_script)
        page.wait_for_timeout(500)

    def test_home_page_with_partial_data(self, page: Page):
        """Test that home page handles partial data (only assets)."""
        page.goto("/home")
        expect(page).to_have_url(re.compile(r".*/home$"))

        # Wait for page to attempt rendering
        page.wait_for_timeout(3000)

        # Page should not crash - main content should be visible
        expect(page.locator(".main-content")).to_be_visible()


class TestInvalidInputHandling:
    """Test that forms handle invalid input gracefully."""

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
        page.wait_for_timeout(1000)

    def test_settings_empty_credentials(self, page: Page):
        """Test that empty credentials show validation error."""
        page.goto("/settings")

        # Click on Data tab
        data_tab = page.get_by_text("Data", exact=True).first
        data_tab.click()
        page.wait_for_timeout(500)

        # Clear credentials
        credentials_textarea = page.locator("textarea").first
        credentials_textarea.fill("")

        # Try to save
        page.locator('button:has-text("Save & Test Configuration")').click()

        # Should show error notification about missing credentials
        expect(page.locator(".q-notification__message")).to_be_visible(timeout=3000)

    def test_settings_malformed_json(self, page: Page):
        """Test that malformed JSON shows validation error."""
        page.goto("/settings")

        # Click on Data tab
        data_tab = page.get_by_text("Data", exact=True).first
        data_tab.click()
        page.wait_for_timeout(500)

        # Fill malformed JSON
        credentials_textarea = page.locator("textarea").first
        credentials_textarea.fill('{"type": "service_account", missing_quote}')

        # Try to save
        page.locator('button:has-text("Save & Test Configuration")').click()

        # Should show error notification about invalid JSON
        expect(page.locator(".q-notification__message:has-text('Invalid JSON')")).to_be_visible(
            timeout=3000
        )

    def test_settings_invalid_url(self, page: Page):
        """Test that invalid URL shows validation error."""
        page.goto("/settings")

        # Click on Data tab
        data_tab = page.get_by_text("Data", exact=True).first
        data_tab.click()
        page.wait_for_timeout(500)

        # Fill invalid URL (keep valid credentials)
        url_input = page.locator('input[placeholder*="spreadsheets"]')
        url_input.fill("not-a-valid-url")

        # Try to save
        page.locator('button:has-text("Save & Test Configuration")').click()

        # Should show error notification about invalid URL
        expect(
            page.locator(".q-notification__message:has-text('Invalid Google Sheets URL')")
        ).to_be_visible(timeout=3000)
