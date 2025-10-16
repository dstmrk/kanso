"""E2E tests for the user settings page."""

import json
import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


class TestUserSettingsPage:
    """Test the user settings page functionality."""

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
        page.locator("textarea").fill(json.dumps(sample_credentials))
        page.locator('button:has-text("Next")').click()
        page.locator('input[placeholder*="spreadsheets"]').fill(sample_sheet_url)
        page.locator('button:has-text("Save & Test Configuration")').click()
        page.wait_for_url(re.compile(r".*/home$"), timeout=10000)

    def test_access_user_settings_page(self, page: Page):
        """Test that user can access the settings page."""
        # Navigate to user settings (this might be through a menu or direct URL)
        page.goto("/user")

        # Check that settings page is displayed (use first to avoid ambiguity with menu items)
        expect(page.locator("text=Advanced Settings").first).to_be_visible()
        expect(page.locator("text=Appearance")).to_be_visible()
        expect(page.locator("text=Google Sheets Configuration")).to_be_visible()

    def test_theme_toggle(self, page: Page):
        """Test that theme toggle works correctly."""
        page.goto("/user")

        # Find the theme toggle
        theme_toggle = page.locator('input[type="checkbox"].toggle')
        expect(theme_toggle).to_be_visible()

        # Get initial theme state
        initial_checked = theme_toggle.is_checked()

        # Click to toggle
        theme_toggle.click()

        # Wait a moment for the change to apply
        page.wait_for_timeout(500)

        # Check that theme changed
        current_checked = theme_toggle.is_checked()
        assert current_checked != initial_checked

    def test_currency_selector(self, page: Page):
        """Test that currency can be changed."""
        page.goto("/user")

        # Find and click the currency dropdown button
        currency_dropdown = page.locator(".dropdown .btn-outline")
        expect(currency_dropdown).to_be_visible()

        # Get current currency
        # initial_currency = currency_dropdown.text_content()

        # Click to open dropdown
        currency_dropdown.click()

        # Select a different currency (e.g., USD) - click on the dropdown menu item, not the button
        page.locator('ul.dropdown-content a:has-text("$ USD")').click()

        # Should show success notification
        expect(page.locator("text=Currency changed")).to_be_visible(timeout=2000)

        # Refresh page and verify currency persisted
        page.reload()
        expect(page.locator('.dropdown .btn-outline:has-text("$ USD")')).to_be_visible()

    def test_update_google_sheets_credentials(
        self, page: Page, sample_credentials: dict, sample_sheet_url: str
    ):
        """Test updating Google Sheets credentials."""
        # Mock API calls
        page.route(
            "**/oauth2.googleapis.com/**", lambda route: route.fulfill(status=200, body="{}")
        )
        page.route(
            "**/sheets.googleapis.com/**", lambda route: route.fulfill(status=200, body="{}")
        )

        page.goto("/user")

        # Find credentials textarea
        credentials_textarea = page.locator("textarea").first
        expect(credentials_textarea).to_be_visible()

        # Update with new credentials
        new_credentials = sample_credentials.copy()
        new_credentials["project_id"] = "updated-project"
        credentials_textarea.fill(json.dumps(new_credentials, indent=2))

        # Find URL input
        url_input = page.locator('input[placeholder*="spreadsheets"]')
        expect(url_input).to_be_visible()

        # Update URL
        new_url = "https://docs.google.com/spreadsheets/d/updated-sheet-id/edit"
        url_input.fill(new_url)

        # Click "Save & Test Configuration"
        page.locator('button:has-text("Save & Test Configuration")').click()

        # Should show success notification
        expect(page.locator("text=Configuration saved")).to_be_visible(timeout=5000)

    def test_invalid_credentials_update(self, page: Page):
        """Test that invalid credentials show appropriate error."""
        page.goto("/user")

        # Find credentials textarea
        credentials_textarea = page.locator("textarea").first

        # Try to save invalid JSON
        credentials_textarea.fill("invalid json {")

        # Click "Save & Test Configuration"
        page.locator('button:has-text("Save & Test Configuration")').click()

        # Should show error notification
        expect(page.locator("text=Invalid JSON")).to_be_visible(timeout=2000)

    def test_credentials_visible_to_user(self, page: Page, sample_credentials: dict):
        """Test that saved credentials are visible in the textarea."""
        page.goto("/user")

        # Find credentials textarea
        credentials_textarea = page.locator("textarea").first
        expect(credentials_textarea).to_be_visible()

        # Check that credentials are pre-filled (they were saved during onboarding)
        credentials_value = credentials_textarea.input_value()
        assert credentials_value.strip() != ""

        # Verify it's valid JSON
        try:
            parsed = json.loads(credentials_value)
            assert "type" in parsed
            assert parsed["type"] == "service_account"
        except json.JSONDecodeError:
            pytest.fail("Credentials textarea does not contain valid JSON")

    def test_missing_url_validation(self, page: Page, sample_credentials: dict):
        """Test that missing URL shows error."""
        page.goto("/user")

        # Clear URL input
        url_input = page.locator('input[placeholder*="spreadsheets"]')
        url_input.fill("")

        # Click "Save & Test Configuration"
        page.locator('button:has-text("Save & Test Configuration")').click()

        # Should show error
        expect(page.locator("text=Please enter a Google Sheet URL")).to_be_visible(timeout=2000)

    def test_invalid_url_format_validation(self, page: Page):
        """Test that invalid URL format shows error."""
        page.goto("/user")

        # Fill invalid URL
        url_input = page.locator('input[placeholder*="spreadsheets"]')
        url_input.fill("https://example.com/not-a-sheet")

        # Click "Save & Test Configuration"
        page.locator('button:has-text("Save & Test Configuration")').click()

        # Should show error
        expect(page.locator("text=Invalid Google Sheets URL")).to_be_visible(timeout=2000)
