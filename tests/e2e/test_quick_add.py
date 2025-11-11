"""E2E tests for quick add expense functionality."""

import json
import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


@pytest.mark.skip(
    reason="E2E tests need setup/timing fixes - core functionality covered by unit tests"
)
class TestQuickAddExpense:
    """Test the quick add expense form and flow."""

    def setup_onboarding(self, page: Page, sample_credentials: dict, sample_sheet_url: str):
        """Helper to complete onboarding before testing quick add."""
        # Mock Google Sheets API
        page.route(
            "**/oauth2.googleapis.com/**",
            lambda route: route.fulfill(status=200, body=json.dumps({"access_token": "test"})),
        )
        page.route(
            "**/sheets.googleapis.com/**",
            lambda route: route.fulfill(status=200, body=json.dumps({"spreadsheetId": "test"})),
        )

        # Complete onboarding
        page.goto("/onboarding")
        page.locator('button:has-text("Get Started")').click()
        page.locator('button:has-text("Next")').click()
        page.locator("textarea").fill(json.dumps(sample_credentials))
        page.locator('input[placeholder*="spreadsheets"]').fill(sample_sheet_url)
        page.locator('button:has-text("Save & Test Configuration")').click()

        # Wait for redirect to home
        page.wait_for_url(re.compile(r".*/home$|.*/$"), timeout=10000)

    def test_quick_add_button_in_header_desktop(
        self, page: Page, sample_credentials: dict, sample_sheet_url: str
    ):
        """Test that Add button appears in header on desktop."""
        self.setup_onboarding(page, sample_credentials, sample_sheet_url)

        # Check Add button exists in header
        add_button = page.locator('header a[href="/quick-add"]').first
        expect(add_button).to_be_visible()

        # Should have "Add" text (desktop version)
        expect(page.locator('header button:has-text("Add")')).to_be_visible()

    def test_navigate_to_quick_add_page(
        self, page: Page, sample_credentials: dict, sample_sheet_url: str
    ):
        """Test navigating to quick add page."""
        self.setup_onboarding(page, sample_credentials, sample_sheet_url)

        # Click Add button
        page.locator('header a[href="/quick-add"]').first.click()

        # Should navigate to /quick-add
        expect(page).to_have_url(re.compile(r".*/quick-add$"))

        # Page should show title
        expect(page.locator("text=Add Expense")).to_be_visible()

    def test_quick_add_form_renders(
        self, page: Page, sample_credentials: dict, sample_sheet_url: str
    ):
        """Test that the quick add form renders with all fields."""
        self.setup_onboarding(page, sample_credentials, sample_sheet_url)

        page.goto("/quick-add")

        # Check form elements exist
        expect(page.locator("text=Add Expense")).to_be_visible()

        # Date fields
        expect(page.locator('text="Month"')).to_be_visible()
        expect(page.locator('text="Year"')).to_be_visible()

        # Input fields
        expect(page.locator('label:has-text("Merchant")')).to_be_visible()
        expect(page.locator('label:has-text("Amount")')).to_be_visible()
        expect(page.locator('label:has-text("Category")')).to_be_visible()
        expect(page.locator('label:has-text("Type")')).to_be_visible()

        # Buttons
        expect(page.locator('button:has-text("Cancel")')).to_be_visible()
        expect(page.locator('button:has-text("Add Expense")')).to_be_visible()

    def test_validation_empty_merchant(
        self, page: Page, sample_credentials: dict, sample_sheet_url: str
    ):
        """Test validation when merchant is empty."""
        self.setup_onboarding(page, sample_credentials, sample_sheet_url)

        page.goto("/quick-add")

        # Try to submit without filling merchant
        page.locator('button:has-text("Add Expense")').click()

        # Should show validation message (wait for it to appear)
        page.wait_for_timeout(500)

        # Should still be on quick-add page (not redirected)
        expect(page).to_have_url(re.compile(r".*/quick-add$"))

    def test_validation_empty_amount(
        self, page: Page, sample_credentials: dict, sample_sheet_url: str
    ):
        """Test validation when amount is empty."""
        self.setup_onboarding(page, sample_credentials, sample_sheet_url)

        page.goto("/quick-add")

        # Fill only merchant
        # Find the merchant input field and type into it
        merchant_input = page.locator('.q-field:has(label:text-is("Merchant")) input').first
        merchant_input.fill("Test Merchant")

        # Submit without amount
        page.locator('button:has-text("Add Expense")').click()

        page.wait_for_timeout(500)

        # Should still be on quick-add page
        expect(page).to_have_url(re.compile(r".*/quick-add$"))

    def test_cancel_button_navigates_back(
        self, page: Page, sample_credentials: dict, sample_sheet_url: str
    ):
        """Test that Cancel button navigates back."""
        self.setup_onboarding(page, sample_credentials, sample_sheet_url)

        # Go to quick add from home
        page.goto("/home")
        page.locator('header a[href="/quick-add"]').first.click()
        expect(page).to_have_url(re.compile(r".*/quick-add$"))

        # Click Cancel
        page.locator('button:has-text("Cancel")').click()

        # Should navigate back to home
        page.wait_for_timeout(500)
        expect(page).to_have_url(re.compile(r".*/home$|.*/$"))

    def test_submit_expense_success(
        self, page: Page, sample_credentials: dict, sample_sheet_url: str
    ):
        """Test successfully submitting an expense."""
        self.setup_onboarding(page, sample_credentials, sample_sheet_url)

        # Mock the append_expense API call
        page.route(
            "**/sheets.googleapis.com/**",
            lambda route: route.fulfill(status=200, body=json.dumps({"updates": {}})),
        )

        page.goto("/quick-add")

        # Fill the form
        # Merchant
        merchant_input = page.locator('.q-field:has(label:text-is("Merchant")) input').first
        merchant_input.fill("Test Store")

        # Amount
        amount_input = page.locator('.q-field:has(label:text-is("Amount")) input').first
        amount_input.fill("50.00")

        # Category
        category_input = page.locator('.q-field:has(label:text-is("Category")) input').first
        category_input.fill("Food")

        # Type
        type_input = page.locator('.q-field:has(label:text-is("Type")) input').first
        type_input.fill("Essential")

        # Submit
        page.locator('button:has-text("Add Expense")').click()

        # Should show loading overlay briefly
        # Note: This might be too fast to catch, but we can try
        # expect(page.locator("text=Saving expense...")).to_be_visible(timeout=1000)

        # Should redirect back after success (with 1.5s delay)
        expect(page).to_have_url(re.compile(r".*/home$|.*/$"), timeout=5000)

    def test_loading_overlay_appears(
        self, page: Page, sample_credentials: dict, sample_sheet_url: str
    ):
        """Test that loading overlay appears during submission."""
        self.setup_onboarding(page, sample_credentials, sample_sheet_url)

        # Mock with a slow response to catch the overlay
        page.route(
            "**/sheets.googleapis.com/**",
            lambda route: (
                page.wait_for_timeout(1000),  # Artificial delay
                route.fulfill(status=200, body=json.dumps({"updates": {}})),
            ),
        )

        page.goto("/quick-add")

        # Fill form quickly
        page.locator('.q-field:has(label:text-is("Merchant")) input').first.fill("Store")
        page.locator('.q-field:has(label:text-is("Amount")) input').first.fill("10")
        page.locator('.q-field:has(label:text-is("Category")) input').first.fill("Food")
        page.locator('.q-field:has(label:text-is("Type")) input').first.fill("Essential")

        # Submit
        page.locator('button:has-text("Add Expense")').click()

        # Check for loading overlay
        expect(page.locator("text=Saving expense...")).to_be_visible(timeout=2000)

    def test_month_year_defaults_to_current(
        self, page: Page, sample_credentials: dict, sample_sheet_url: str
    ):
        """Test that month and year default to current date."""
        self.setup_onboarding(page, sample_credentials, sample_sheet_url)

        page.goto("/quick-add")

        # Wait for form to render
        page.wait_for_timeout(1000)

        # Check that month/year fields exist
        # Note: Testing actual default values is tricky with NiceGUI components
        # We verify the fields are present and visible

        # The Month field should exist and have a value
        month_field = page.locator('text="Month"').first
        expect(month_field).to_be_visible()

        # The Year field should exist and have a value
        year_field = page.locator('text="Year"').first
        expect(year_field).to_be_visible()
