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

    def test_quick_add_cancel_navigates_back(self, page: Page):
        """Test that Cancel button on Quick Add navigates back."""
        # Navigate directly to quick-add
        page.goto("/quick-add")
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

        # Logout button should be visible in Account tab (default tab)
        logout_button = page.locator('button:has-text("Logout")')
        expect(logout_button).to_be_visible()
        logout_button.click()

        # Should redirect to onboarding or logout page
        expect(page).to_have_url(re.compile(r".*/onboarding$|.*/logout$"), timeout=5000)


class TestDirectPageAccess:
    """Test that pages can be accessed directly via URL."""

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

    def test_direct_access_home(self, page: Page):
        """Test direct URL access to Home page."""
        page.goto("/home")
        expect(page).to_have_url(re.compile(r".*/home$"))
        # Page should load without crashing
        page.wait_for_timeout(2000)

    def test_direct_access_net_worth(self, page: Page):
        """Test direct URL access to Net Worth page."""
        page.goto("/net-worth")
        expect(page).to_have_url(re.compile(r".*/net-worth$"))
        # Page should load without crashing
        page.wait_for_timeout(2000)

    def test_direct_access_expenses(self, page: Page):
        """Test direct URL access to Expenses page."""
        page.goto("/expenses")
        expect(page).to_have_url(re.compile(r".*/expenses$"))
        # Page should load without crashing
        page.wait_for_timeout(2000)

    def test_direct_access_quick_add(self, page: Page):
        """Test direct URL access to Quick Add page."""
        page.goto("/quick-add")
        expect(page).to_have_url(re.compile(r".*/quick-add$"))
        # Page should show Add Expense title
        expect(page.get_by_text("Add Expense").first).to_be_visible()

    def test_direct_access_settings(self, page: Page):
        """Test direct URL access to Settings page."""
        page.goto("/settings")
        expect(page).to_have_url(re.compile(r".*/settings$"))
        # Page should show settings tabs
        expect(page.get_by_text("Account", exact=True).first).to_be_visible()
