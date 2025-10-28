from nicegui import app, ui


def render() -> None:
    """Render the onboarding page with stepper for first-time setup."""
    # Redirect to home if onboarding already completed
    if app.storage.general.get("onboarding_completed"):
        ui.navigate.to("/home")
        return

    with ui.column().classes("w-full min-h-screen flex items-center justify-center p-4"):
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
                    ui.label("Credentials")

                step3 = ui.element("li").classes("step")
                with step3:
                    ui.label("Configuration")

            # Content card
            with ui.card().classes("w-full p-8"):
                # Step 1: Welcome
                step1_content = ui.column().classes("w-full")
                with step1_content:
                    ui.label("🎉 Welcome to your first setup!").classes("text-2xl font-bold mb-4")
                    ui.label(
                        "Kanso helps you visualize and track your personal finances using Google Sheets as your data source."
                    ).classes("text-base mb-4")

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
                            "btn bg-secondary hover:bg-secondary/80 text-secondary-content"
                        )

                # Step 2: Credentials
                step2_content = ui.column().classes("w-full hidden")
                with step2_content:
                    ui.label("📋 Google Service Account Credentials").classes(
                        "text-2xl font-bold mb-4"
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

                    credentials_textarea = (
                        ui.textarea(
                            label="Paste your credentials JSON here",
                            placeholder='{\n  "type": "service_account",\n  "project_id": "...",\n  ...\n}',
                            value="",
                        )
                        .classes("w-full font-mono text-sm")
                        .style("min-height: 300px")
                    )

                    with ui.row().classes("w-full justify-between mt-8"):
                        ui.button("← Back", on_click=lambda: go_to_step(1)).classes(
                            "btn btn-outline"
                        )
                        ui.button("Next →", on_click=lambda: go_to_step(3)).classes(
                            "btn bg-secondary hover:bg-secondary/80 text-secondary-content"
                        )

                # Step 3: Sheet URL & Save
                step3_content = ui.column().classes("w-full hidden")
                with step3_content:
                    ui.label("🔗 Google Sheet Configuration").classes("text-2xl font-bold mb-4")

                    ui.label(
                        "Enter the URL of your Google Sheet where your financial data is stored."
                    ).classes("text-base mb-4")

                    url_input = ui.input(
                        label="Google Sheet URL",
                        placeholder="https://docs.google.com/spreadsheets/d/...",
                        value="",
                    ).classes("w-full")

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

                # Validate both are present
                if not credentials_content:
                    ui.notify("✗ Please paste the credentials JSON", type="negative")
                    return

                if not url:
                    ui.notify("✗ Please enter a Google Sheet URL", type="negative")
                    return

                # Validate credentials JSON
                try:
                    json_data = json.loads(credentials_content)
                except json.JSONDecodeError:
                    ui.notify("✗ Invalid JSON! Please check the format.", type="negative")
                    return

                # Validate it looks like a service account credential
                if "type" not in json_data or json_data.get("type") != "service_account":
                    ui.notify(
                        "✗ This doesn't look like a service account credential", type="negative"
                    )
                    return

                # Validate URL format
                if not url.startswith("https://docs.google.com/spreadsheets/"):
                    ui.notify("✗ Invalid Google Sheets URL format", type="negative")
                    return

                # Save to general storage (shared across devices)
                app.storage.general["google_credentials_json"] = credentials_content
                app.storage.general["custom_workbook_url"] = url
                app.storage.general["onboarding_completed"] = True

                # Quick validation test (non-blocking)
                try:
                    from app.services.google_sheets import GoogleSheetService

                    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=True) as tmp:
                        json.dump(json_data, tmp, indent=2)
                        tmp.flush()
                        tmp_path = Path(tmp.name)

                        # Test connection (don't need to store the service)
                        GoogleSheetService(tmp_path, url)
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
