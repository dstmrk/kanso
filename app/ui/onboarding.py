from nicegui import app, ui

from app.core.constants import CURRENCY_OPTIONS_FULL
from app.core.validators import (
    clean_google_sheets_url,
    validate_google_credentials_json,
    validate_google_sheets_url,
)
from app.services import utils
from app.ui.styles import (
    ONBOARDING_HEADING_CLASSES,
    ONBOARDING_PARAGRAPH_CLASSES,
    ONBOARDING_SECONDARY_BUTTON_CLASSES,
)


def render() -> None:
    """Render the onboarding page with stepper for first-time setup."""
    # Redirect to home if onboarding already completed
    if app.storage.general.get("onboarding_completed"):
        ui.navigate.to("/home")
        return

    # Mobile-only message (hidden on desktop/tablet)
    with ui.column().classes("w-full min-h-screen flex items-center justify-center p-6 md:hidden"):
        with ui.card().classes("max-w-md p-8"):
            with ui.column().classes("items-center gap-4 text-center"):
                ui.icon("desktop_windows", size="56px").classes("text-base-content/40")
                ui.label("Desktop Required").classes("text-2xl font-bold text-base-content")
                ui.label(
                    "Kanso's onboarding is currently optimized for desktop and tablet browsers."
                ).classes("text-base text-base-content/70")

    # Desktop/tablet wizard (visible by default, hidden on mobile <768px)
    with ui.column().classes("w-full min-h-screen items-center justify-center p-4 max-md:hidden"):
        with ui.column().classes("w-full max-w-4xl"):
            # Header
            ui.label("Welcome to Kanso").classes("text-4xl font-bold text-center mb-2")
            ui.label("Personal Finance Dashboard").classes("text-xl text-center mb-8 opacity-70")

            # Stepper (horizontal)
            with ui.element("ul").classes("steps w-full mb-8"):
                step1 = ui.element("li").classes("step step-primary")
                with step1:
                    ui.label("Welcome")

                step2 = ui.element("li").classes("step")
                with step2:
                    ui.label("Currency")

                step3 = ui.element("li").classes("step")
                with step3:
                    ui.label("Google Sheets")

            # Content card
            with ui.card().classes("w-full p-8"):
                # Step 1: Welcome
                step1_content = ui.column().classes("w-full")
                with step1_content:
                    ui.label("🎉 Welcome to your first setup!").classes(ONBOARDING_HEADING_CLASSES)
                    ui.label(
                        "Kanso helps you visualize and track your personal finances using Google Sheets as your data source."
                    ).classes(ONBOARDING_PARAGRAPH_CLASSES)

                    ui.label("To get started, you'll need:").classes("text-lg font-semibold mb-2")
                    with ui.column().classes("gap-2 ml-4"):
                        ui.label(
                            "✓ A Google Cloud service account with credentials (JSON file)"
                        ).classes("text-base")
                        ui.label("✓ A Google Sheet to store your financial data").classes(
                            "text-base"
                        )

                    ui.label(
                        "Don't worry, we'll guide you through the setup process step by step!"
                    ).classes("text-base mt-4 opacity-70")

                    with ui.row().classes("w-full justify-end mt-8"):
                        ui.button("Get Started", on_click=lambda: go_to_step(2)).classes(
                            ONBOARDING_SECONDARY_BUTTON_CLASSES
                        )

                # Step 2: Currency Selection
                step2_content = ui.column().classes("w-full hidden")
                with step2_content:
                    ui.label("💱 Currency Preference").classes(ONBOARDING_HEADING_CLASSES)

                    ui.label(
                        "Select your preferred currency for displaying amounts throughout the app."
                    ).classes(ONBOARDING_PARAGRAPH_CLASSES)

                    # Auto-detect currency from browser locale
                    detected_currency = "USD"  # Fallback default

                    async def detect_and_set_currency():
                        """Detect browser locale and set currency automatically."""
                        # Get browser locale via JavaScript
                        browser_locale = await ui.run_javascript("navigator.language")
                        if browser_locale:
                            detected = utils.get_currency_from_browser_locale(browser_locale)
                            currency_select.value = detected

                    currency_select = ui.select(
                        label="Currency",
                        options=CURRENCY_OPTIONS_FULL,
                        value=detected_currency,
                    ).classes("w-full")

                    # Trigger auto-detection after UI is ready
                    ui.timer(0.1, detect_and_set_currency, once=True)

                    ui.label("You can change this later in settings.").classes(
                        "text-sm mt-4 opacity-70"
                    )

                    with ui.row().classes("w-full justify-between mt-8"):
                        ui.button("← Back", on_click=lambda: go_to_step(1)).classes(
                            "btn btn-outline"
                        )
                        ui.button("Next →", on_click=lambda: go_to_step(3)).classes(
                            ONBOARDING_SECONDARY_BUTTON_CLASSES
                        )

                # Step 3: Google Sheets Configuration (Credentials + Sheet URL)
                step3_content = ui.column().classes("w-full hidden")
                with step3_content:
                    ui.label("📋 Google Sheets Configuration").classes(ONBOARDING_HEADING_CLASSES)

                    ui.label(
                        "Connect Kanso to your Google Sheet with your financial data."
                    ).classes(ONBOARDING_PARAGRAPH_CLASSES)

                    # Credentials section
                    ui.label("1. Service Account Credentials").classes(
                        "text-lg font-semibold mt-4 mb-2"
                    )
                    ui.label(
                        "You need a service account JSON file from Google Cloud to access your spreadsheet."
                    ).classes("text-base mb-2")

                    with ui.row().classes("gap-2 items-center mb-4"):
                        ui.label("Need help getting credentials?").classes("text-sm")
                        ui.link(
                            "Follow this guide →",
                            "https://docs.gspread.org/en/latest/oauth2.html#service-account",
                            new_tab=True,
                        ).classes("text-sm text-primary underline")

                    # Credentials textarea label (external, theme-aware)
                    ui.label("Paste your credentials JSON here").classes(
                        "text-base-content font-semibold mt-4"
                    )

                    credentials_textarea = (
                        ui.textarea(
                            placeholder='{\n  "type": "service_account",\n  "project_id": "...",\n  ...\n}',
                            value="",
                        )
                        .classes("w-full font-mono text-sm mt-2")
                        .style("min-height: 250px")
                    )

                    # Sheet URL section
                    ui.label("2. Google Sheet URL").classes("text-lg font-semibold mt-6 mb-2")
                    ui.label(
                        "Enter the URL of your Google Sheet where your financial data is stored."
                    ).classes(ONBOARDING_PARAGRAPH_CLASSES)

                    # Sheet URL input label (external, theme-aware)
                    ui.label("Google Sheet URL").classes("text-base-content font-semibold mt-4")

                    url_input = ui.input(
                        placeholder="https://docs.google.com/spreadsheets/d/...",
                        value="",
                    ).classes("w-full mt-2")

                    with ui.row().classes("w-full justify-between mt-8"):
                        ui.button("← Back", on_click=lambda: go_to_step(2)).classes(
                            "btn btn-outline"
                        )
                        ui.button(
                            "Save & Test Configuration", on_click=lambda: save_and_complete()
                        ).classes("btn bg-secondary hover:bg-secondary/80 text-secondary-content")

            def go_to_step(step: int):
                """Navigate to a specific step."""
                # Update stepper visual
                if step >= 1:
                    step1.classes(add="step-primary")
                else:
                    step1.classes(remove="step-primary")

                if step >= 2:
                    step2.classes(add="step-primary")
                else:
                    step2.classes(remove="step-primary")

                if step >= 3:
                    step3.classes(add="step-primary")
                else:
                    step3.classes(remove="step-primary")

                # Show/hide content
                if step == 1:
                    step1_content.classes(remove="hidden")
                    step2_content.classes(add="hidden")
                    step3_content.classes(add="hidden")
                elif step == 2:
                    step1_content.classes(add="hidden")
                    step2_content.classes(remove="hidden")
                    step3_content.classes(add="hidden")
                elif step == 3:
                    step1_content.classes(add="hidden")
                    step2_content.classes(add="hidden")
                    step3_content.classes(remove="hidden")

            def save_and_complete():
                """Validate, save and test configuration, then complete onboarding."""
                import json
                import tempfile
                from pathlib import Path

                # Get values directly from inputs
                credentials_content = credentials_textarea.value.strip()
                url = url_input.value.strip()
                selected_currency = currency_select.value

                # Validate all fields are present
                if not credentials_content:
                    ui.notify("✗ Please paste the credentials JSON", type="negative")
                    return

                if not url:
                    ui.notify("✗ Please enter a Google Sheet URL", type="negative")
                    return

                if not selected_currency:
                    ui.notify("✗ Please select a currency", type="negative")
                    return

                # Validate credentials JSON using centralized validator
                is_valid_creds, creds_result = validate_google_credentials_json(credentials_content)
                if not is_valid_creds:
                    ui.notify(f"✗ {creds_result}", type="negative")
                    return

                json_data = creds_result  # creds_result is the parsed JSON dict

                # Validate and clean URL using centralized validators
                is_valid_url, url_error = validate_google_sheets_url(url)
                if not is_valid_url:
                    ui.notify(f"✗ {url_error}", type="negative")
                    return

                # Clean URL to extract only workbook ID (removes query params, fragments)
                try:
                    clean_url = clean_google_sheets_url(url)
                except ValueError as e:
                    ui.notify(f"✗ {str(e)}", type="negative")
                    return

                # Save to general storage (shared across devices)
                app.storage.general["google_credentials_json"] = credentials_content
                app.storage.general["custom_workbook_url"] = clean_url
                app.storage.general["currency"] = selected_currency
                app.storage.general["onboarding_completed"] = True

                # Quick validation test (non-blocking)
                try:
                    from app.services.google_sheets import GoogleSheetService

                    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=True) as tmp:
                        json.dump(json_data, tmp, indent=2)
                        tmp.flush()
                        tmp_path = Path(tmp.name)

                        # Test connection with cleaned URL
                        GoogleSheetService(tmp_path, clean_url)
                        ui.notify(
                            "✓ Configuration saved! Redirecting to dashboard...", type="positive"
                        )

                except Exception as e:
                    ui.notify(
                        f"⚠ Configuration saved, but connection test failed: {str(e)}",
                        type="warning",
                    )

                # Redirect immediately to home - data will load with placeholders
                ui.navigate.to("/")
