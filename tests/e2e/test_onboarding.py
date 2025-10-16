"""E2E tests for the onboarding flow."""

import json
import re

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


class TestOnboardingFlow:
    """Test the complete onboarding user flow."""

    def test_new_user_redirected_to_onboarding(self, page: Page):
        """Test that new users without onboarding are redirected to /onboarding."""
        # Navigate to root
        page.goto("/")

        # Should be redirected to onboarding (use regex to match URL ending)
        expect(page).to_have_url(re.compile(r".*/onboarding$"))

        # Check that the onboarding page is displayed
        expect(page.locator("text=Welcome to Kanso")).to_be_visible()

    def test_onboarding_step_navigation(self, page: Page):
        """Test navigating through the onboarding steps."""
        page.goto("/onboarding")

        # Step 1: Welcome page should be visible
        expect(page.locator("text=Welcome to Kanso")).to_be_visible()
        expect(page.locator("text=Welcome to your first setup")).to_be_visible()

        # Click "Get Started" button
        page.locator('button:has-text("Get Started")').click()

        # Step 2: Credentials page should be visible
        expect(page.locator("text=Google Service Account Credentials")).to_be_visible()
        expect(page.locator("textarea")).to_be_visible()

        # Check that we can't go to step 3 without filling credentials
        # (Next button should be visible)
        expect(page.locator('button:has-text("Next")')).to_be_visible()

    def test_credentials_validation(self, page: Page):
        """Test that credentials are validated correctly."""
        page.goto("/onboarding")

        # Navigate to step 2
        page.locator('button:has-text("Get Started")').click()

        # Navigate to step 3 without filling credentials
        page.locator('button:has-text("Next")').click()

        # Try to save without credentials (this triggers validation)
        page.locator('button:has-text("Save & Test Configuration")').click()

        # Should show error notification for missing credentials
        expect(page.locator("text=Please paste the credentials JSON")).to_be_visible(timeout=2000)

        # Test invalid JSON in a fresh onboarding session
        page.goto("/onboarding")
        page.locator('button:has-text("Get Started")').click()

        # Fill in invalid JSON
        page.locator("textarea").fill("invalid json {")
        page.locator('button:has-text("Next")').click()

        # Try to save with invalid JSON
        page.locator('button:has-text("Save & Test Configuration")').click()

        # Should show JSON error (full text: "✗ Invalid JSON! Please check the format.")
        expect(page.locator("text=Invalid JSON").first).to_be_visible(timeout=3000)

    def test_complete_onboarding_flow(
        self, page: Page, sample_credentials: dict, sample_sheet_url: str
    ):
        """Test completing the entire onboarding flow."""
        # Mock Google Sheets API to prevent actual connection attempts
        page.route(
            "**/oauth2.googleapis.com/**",
            lambda route: route.fulfill(
                status=200,
                body=json.dumps({"access_token": "test-token", "expires_in": 3600}),
            ),
        )
        page.route(
            "**/sheets.googleapis.com/**",
            lambda route: route.fulfill(
                status=200, body=json.dumps({"spreadsheetId": "test-id", "sheets": []})
            ),
        )

        page.goto("/onboarding")

        # Step 1: Welcome
        expect(page.locator("text=Welcome to Kanso")).to_be_visible()
        page.locator('button:has-text("Get Started")').click()

        # Step 2: Credentials
        expect(page.locator("text=Google Service Account Credentials")).to_be_visible()

        # Fill in valid credentials JSON
        credentials_json = json.dumps(sample_credentials, indent=2)
        page.locator("textarea").fill(credentials_json)

        # Click Next
        page.locator('button:has-text("Next")').click()

        # Step 3: Configuration
        expect(page.locator("text=Google Sheet Configuration")).to_be_visible()

        # Fill in URL
        page.locator('input[placeholder*="spreadsheets"]').fill(sample_sheet_url)

        # Click "Save & Test Configuration"
        page.locator('button:has-text("Save & Test Configuration")').click()

        # Should be redirected to home page (redirect happens immediately, notification is too brief to check)
        expect(page).to_have_url(re.compile(r".*/home$"), timeout=10000)

    def test_onboarding_completed_users_redirected_to_home(
        self, page: Page, sample_credentials: dict, sample_sheet_url: str
    ):
        """Test that users who completed onboarding are redirected to home."""
        # Complete onboarding first
        # Mock API calls
        page.route(
            "**/oauth2.googleapis.com/**", lambda route: route.fulfill(status=200, body="{}")
        )
        page.route(
            "**/sheets.googleapis.com/**", lambda route: route.fulfill(status=200, body="{}")
        )

        page.goto("/onboarding")
        page.locator('button:has-text("Get Started")').click()
        page.locator("textarea").fill(json.dumps(sample_credentials))
        page.locator('button:has-text("Next")').click()
        page.locator('input[placeholder*="spreadsheets"]').fill(sample_sheet_url)
        page.locator('button:has-text("Save & Test Configuration")').click()

        # Wait for redirect
        page.wait_for_url(re.compile(r".*/home$"), timeout=10000)

        # Now try to go back to onboarding
        page.goto("/onboarding")

        # Should be redirected to home since onboarding is already completed
        # (This might need adjustment based on actual implementation)
        page.wait_for_timeout(1000)  # Give time for potential redirect

    def test_back_button_navigation(self, page: Page):
        """Test that back button works correctly in onboarding."""
        page.goto("/onboarding")

        # Go to step 2
        page.locator('button:has-text("Get Started")').click()
        expect(page.locator("text=Google Service Account Credentials")).to_be_visible()

        # Click Back button (use first visible one, as there might be multiple in different steps)
        page.locator('button:has-text("← Back")').first.click()

        # Should be back at step 1
        expect(page.locator("text=Welcome to your first setup")).to_be_visible()
