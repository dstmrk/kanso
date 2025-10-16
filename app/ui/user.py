from nicegui import app, ui

from app.services.utils import get_user_currency
from app.ui import dock, header, styles

# Currency options with symbol and code only
CURRENCY_OPTIONS = {"EUR": "€ EUR", "USD": "$ USD", "GBP": "£ GBP", "CHF": "Fr CHF", "JPY": "¥ JPY"}


def render() -> None:
    """Render the advanced settings page for data management."""
    header.render()

    with ui.column().classes("w-full max-w-screen-xl mx-auto p-4 space-y-5 main-content"):
        # Page title
        ui.label("Advanced Settings").classes("text-3xl font-bold")
        ui.separator()

        # Appearance section
        with ui.column().classes("gap-4 mt-4"):
            ui.label("Appearance").classes("text-xl font-semibold")

            # Theme toggle
            def save_theme_preference() -> None:
                current_theme: str = app.storage.user.get("theme", "light")
                new_theme: str = "dark" if current_theme == "light" else "light"
                app.storage.user["theme"] = new_theme

                # Update echarts theme URL for charts
                app.storage.user["echarts_theme_url"] = (
                    styles.DEFAULT_ECHART_THEME_FOLDER
                    + new_theme
                    + styles.DEFAULT_ECHARTS_THEME_SUFFIX
                )

                # Update localStorage and DOM immediately
                script: str = f"""
                    localStorage.setItem('kanso-theme', '{new_theme}');
                    document.documentElement.setAttribute('data-theme', '{new_theme}');
                    document.documentElement.style.colorScheme = '{new_theme}';
                """
                ui.run_javascript(script)

            with ui.row().classes("items-center gap-4"):
                ui.label("Theme:").classes("text-base")
                with ui.element("label").classes("flex cursor-pointer gap-2 items-center"):
                    ui.html(styles.SUN_SVG, sanitize=False)
                    toggle = (
                        ui.element("input")
                        .props('type="checkbox" value="dark"')
                        .classes("toggle")
                        .on("click", save_theme_preference)
                    )
                    current_theme: str = app.storage.user.get("theme", "light")
                    if current_theme == "dark":
                        toggle.props("checked")
                    ui.html(styles.MOON_SVG, sanitize=False)

            # Currency selector
            def save_currency_preference(event) -> None:
                """Save the selected currency preference."""
                selected_code = event.value
                app.storage.user["currency"] = selected_code
                ui.notify(f"Currency changed to {CURRENCY_OPTIONS[selected_code]}", type="positive")

            # Get current currency: use stored preference or detect from locale
            current_currency: str = app.storage.user.get("currency", get_user_currency())
            # Save it if it wasn't stored yet
            if "currency" not in app.storage.user:
                app.storage.user["currency"] = current_currency

            with ui.row().classes("items-center gap-4 mt-4"):
                ui.label("Currency:").classes("text-base")
                # DaisyUI dropdown component
                with ui.element("div").classes("dropdown dropdown-end"):
                    # Dropdown button showing current selection
                    current_label = CURRENCY_OPTIONS[current_currency]
                    dropdown_btn = (
                        ui.element("div")
                        .props('tabindex="0" role="button"')
                        .classes("btn btn-outline w-48")
                    )
                    with dropdown_btn:
                        label_display = ui.label(current_label).classes("mx-auto")

                    # Dropdown menu
                    with (
                        ui.element("ul")
                        .props('tabindex="0"')
                        .classes(
                            "dropdown-content menu bg-base-100 rounded-box z-[1] w-48 p-2 shadow mt-2 right-0"
                        )
                    ):
                        for code, label in CURRENCY_OPTIONS.items():
                            with ui.element("li"):

                                def make_click_handler(currency_code, label_text):
                                    def handler():
                                        save_currency_preference(
                                            type("Event", (), {"value": currency_code})()
                                        )
                                        label_display.set_text(label_text)
                                        # Close dropdown by removing focus
                                        ui.run_javascript("document.activeElement.blur()")

                                    return handler

                                link = ui.element("a")
                                with link:
                                    ui.label(label)
                                link.on("click", make_click_handler(code, label))

        # Google Sheets Configuration section
        with ui.column().classes("gap-4 mt-6"):
            ui.label("Google Sheets Configuration").classes("text-xl font-semibold")

            # Credentials JSON textarea
            ui.label("Google Service Account Credentials JSON:").classes("text-base mt-2")

            # Get existing credentials if any
            existing_creds = app.storage.user.get("google_credentials_json", "")

            credentials_textarea = (
                ui.textarea(
                    label="Paste your credentials JSON here",
                    placeholder='{\n  "type": "service_account",\n  "project_id": "...",\n  ...\n}',
                    value=existing_creds,
                )
                .classes("w-full font-mono text-sm")
                .style("min-height: 200px")
            )

            # Workbook URL input
            ui.label("Google Sheet URL:").classes("text-base mt-4")
            current_url = app.storage.user.get("custom_workbook_url", "")

            url_input = ui.input(
                label="Workbook URL",
                placeholder="https://docs.google.com/spreadsheets/d/...",
                value=current_url,
            ).classes("w-full max-w-md")

            async def save_and_test_configuration():
                """Validate, save and test both credentials and URL."""
                import json
                import tempfile
                from pathlib import Path

                # Get values
                credentials_content = credentials_textarea.value.strip()
                url_value = url_input.value.strip()

                # Validate both are present
                if not credentials_content:
                    ui.notify("✗ Please paste the credentials JSON", type="negative")
                    return

                if not url_value:
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

                # Validate URL format (basic check for Google Sheets URL)
                if not url_value.startswith("https://docs.google.com/spreadsheets/"):
                    ui.notify("✗ Invalid Google Sheets URL format", type="negative")
                    return

                # Data is valid - save to storage
                app.storage.user["google_credentials_json"] = credentials_content
                app.storage.user["custom_workbook_url"] = url_value

                # Now test the connection
                try:
                    from app.services.google_sheets import GoogleSheetService

                    # Create a temporary file with the credentials
                    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
                        json.dump(json_data, tmp, indent=2)
                        tmp_path = Path(tmp.name)

                    try:
                        # Try to connect (don't need to store the service)
                        GoogleSheetService(tmp_path, url_value)
                        ui.notify("✓ Configuration saved and connection verified!", type="positive")
                    finally:
                        # Clean up temp file
                        tmp_path.unlink(missing_ok=True)

                except Exception as e:
                    ui.notify(
                        f"⚠ Configuration saved, but connection failed: {str(e)}", type="warning"
                    )

            ui.button("Save & Test Configuration", on_click=save_and_test_configuration).classes(
                "btn bg-secondary hover:bg-secondary/80 text-secondary-content mt-2"
            )

    dock.render()
