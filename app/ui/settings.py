from nicegui import app, ui

from app.core.constants import APP_VERSION, CURRENCY_OPTIONS_SHORT
from app.core.state_manager import state_manager
from app.core.validators import (
    clean_google_sheets_url,
    validate_google_credentials_json,
    validate_google_sheets_url,
)
from app.services import pages, utils
from app.services.data_loader import refresh_all_data
from app.services.utils import get_user_currency
from app.ui import header, styles


def render() -> None:
    """Render the settings page with tabs for Account, Data, and About."""
    header.render()

    with ui.column().classes("w-full max-w-screen-xl mx-auto p-4 space-y-5 main-content"):
        # Page title
        ui.label("Settings").classes("text-3xl font-bold")
        ui.separator()

        # Tabs navigation (clean style with border, no background box)
        with ui.tabs().classes("w-full tabs tabs-bordered") as tabs:
            account_tab = ui.tab("Account")
            data_tab = ui.tab("Data")
            about_tab = ui.tab("About")

        # Tab panels (full width, bg-base-100 for theme support)
        with ui.tab_panels(tabs, value=account_tab).classes("w-full mt-6 bg-base-100"):
            # ========== Account Tab ==========
            with ui.tab_panel(account_tab):
                with ui.column().classes("w-full gap-6"):
                    # Appearance section
                    ui.label("Appearance").classes("text-xl font-semibold")

                    # Theme toggle
                    def save_theme_preference() -> None:
                        current_theme: str = app.storage.general.get("theme", "light")
                        new_theme: str = "dark" if current_theme == "light" else "light"
                        app.storage.general["theme"] = new_theme

                        # Update echarts theme URL for charts
                        app.storage.general["echarts_theme_url"] = (
                            styles.DEFAULT_ECHART_THEME_FOLDER
                            + new_theme
                            + styles.DEFAULT_ECHARTS_THEME_SUFFIX
                        )

                        # Update localStorage and DOM, then reload
                        script: str = f"""
                            localStorage.setItem('kanso-theme', '{new_theme}');
                            document.documentElement.setAttribute('data-theme', '{new_theme}');
                            document.documentElement.style.colorScheme = '{new_theme}';
                            setTimeout(() => window.location.reload(), 100);
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
                            current_theme: str = app.storage.general.get("theme", "light")
                            if current_theme == "dark":
                                toggle.props("checked")
                            ui.html(styles.MOON_SVG, sanitize=False)

                    # Currency selector
                    def save_currency_preference(event) -> None:
                        """Save the selected currency preference."""
                        selected_code = event.value
                        app.storage.general["currency"] = selected_code
                        ui.notify(
                            f"Currency changed to {CURRENCY_OPTIONS_SHORT[selected_code]}",
                            type="positive",
                        )

                    # Get current currency: use stored preference or detect from locale
                    current_currency: str = app.storage.general.get("currency", get_user_currency())
                    # Save it if it wasn't stored yet
                    if "currency" not in app.storage.general:
                        app.storage.general["currency"] = current_currency

                    with ui.row().classes("items-center gap-4 mt-4"):
                        ui.label("Currency:").classes("text-base")
                        # DaisyUI dropdown component with scrollable menu
                        with ui.element("div").classes("dropdown dropdown-end"):
                            # Dropdown button showing current selection
                            current_label = CURRENCY_OPTIONS_SHORT[current_currency]
                            dropdown_btn = (
                                ui.element("div")
                                .props('tabindex="0" role="button"')
                                .classes("btn btn-outline w-48")
                            )
                            with dropdown_btn:
                                label_display = ui.label(current_label).classes("mx-auto")

                            # Dropdown menu with scroll (max 15rem height ~ 240px)
                            with (
                                ui.element("ul")
                                .props('tabindex="0"')
                                .classes(
                                    "dropdown-content menu bg-base-100 rounded-box z-[100] w-48 p-2 shadow mt-2 right-0 max-h-60 overflow-y-auto"
                                )
                            ):
                                for code, label in CURRENCY_OPTIONS_SHORT.items():
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

                    # Account Actions section
                    ui.separator().classes("my-6")
                    ui.label("Account").classes("text-xl font-semibold")

                    # Logout button
                    with (
                        ui.element("button")
                        .on("click", lambda: ui.navigate.to(pages.LOGOUT_PAGE))
                        .classes("btn btn-outline btn-error w-full max-w-xs")
                    ):
                        ui.label("Logout")

            # ========== Data Tab ==========
            with ui.tab_panel(data_tab):
                with ui.column().classes("w-full gap-6"):
                    # Google Sheets Configuration section
                    ui.label("Google Sheets Configuration").classes("text-xl font-semibold")

                    # Credentials JSON textarea
                    ui.label("Google Service Account Credentials JSON:").classes(
                        "text-base-content font-semibold mt-4"
                    )

                    # Get existing credentials if any
                    existing_creds = app.storage.general.get("google_credentials_json", "")

                    credentials_textarea = (
                        ui.textarea(
                            placeholder='{\n  "type": "service_account",\n  "project_id": "...",\n  ...\n}',
                            value=existing_creds,
                        )
                        .classes("w-full font-mono text-sm mt-2")
                        .style("min-height: 200px")
                    )

                    # Workbook URL input
                    ui.label("Google Sheet URL:").classes("text-base-content font-semibold mt-6")
                    current_url = app.storage.general.get("custom_workbook_url", "")

                    url_input = ui.input(
                        placeholder="https://docs.google.com/spreadsheets/d/...",
                        value=current_url,
                    ).classes("w-full max-w-2xl mt-2")

                    async def save_and_test_configuration():
                        """Validate, save and test both credentials and URL."""
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

                        # Validate credentials JSON using centralized validator
                        is_valid_creds, creds_result = validate_google_credentials_json(
                            credentials_content
                        )
                        if not is_valid_creds:
                            ui.notify(f"✗ {creds_result}", type="negative")
                            return

                        # Validate and clean URL using centralized validators
                        is_valid_url, url_error = validate_google_sheets_url(url_value)
                        if not is_valid_url:
                            ui.notify(f"✗ {url_error}", type="negative")
                            return

                        # Clean URL to extract only workbook ID
                        try:
                            clean_url = clean_google_sheets_url(url_value)
                        except ValueError as e:
                            ui.notify(f"✗ {str(e)}", type="negative")
                            return

                        # Data is valid - save to general storage
                        app.storage.general["google_credentials_json"] = credentials_content
                        app.storage.general["custom_workbook_url"] = clean_url

                        # Clear all cached sheets and computed data
                        for sheet_key in [
                            "assets_sheet",
                            "liabilities_sheet",
                            "expenses_sheet",
                            "incomes_sheet",
                        ]:
                            if sheet_key in app.storage.general:
                                del app.storage.general[sheet_key]
                                state_manager.invalidate_cache(sheet_key)

                        # Test the connection with cleaned URL
                        try:
                            # Test connection using temporary sheet service
                            with utils.temporary_sheet_service(credentials_content, clean_url):
                                # Connection successful if no exception raised
                                ui.notify(
                                    "✓ Configuration saved and connection verified!",
                                    type="positive",
                                )
                        except Exception as e:
                            ui.notify(
                                f"⚠ Configuration saved, but connection failed: {str(e)}",
                                type="warning",
                            )

                    ui.button(
                        "Save & Test Configuration", on_click=save_and_test_configuration
                    ).classes("btn bg-secondary hover:bg-secondary/80 text-secondary-content mt-2")

                    # Data Management section
                    ui.separator().classes("my-6")
                    ui.label("Data Management").classes("text-xl font-semibold")

                    # Refresh Data button
                    async def refresh_data() -> None:
                        """Force refresh all data from Google Sheets and clear cache."""
                        # Show loading state
                        with ui.dialog() as loading_dialog, ui.card():
                            ui.label("Refreshing data from Google Sheets...")
                            ui.spinner(size="lg")

                        loading_dialog.open()

                        try:
                            # Refresh data from Google Sheets
                            results = await refresh_all_data()

                            # Close loading dialog
                            loading_dialog.close()

                            # Clear cache after successful refresh
                            state_manager.invalidate_cache()

                            # Show results dialog
                            with ui.dialog() as result_dialog, ui.card().classes("gap-4"):
                                ui.label("Data Refresh Complete").classes("text-xl font-bold")

                                # Check if there was an error
                                if "error" in results:
                                    ui.label(f"Error: {results['error']}").classes("text-error")
                                else:
                                    # Show summary
                                    summary = f"✓ {results['updated_count']} sheet(s) updated"
                                    if results["unchanged_count"] > 0:
                                        summary += (
                                            f"\n• {results['unchanged_count']} sheet(s) unchanged"
                                        )
                                    if results["failed_count"] > 0:
                                        summary += f"\n✗ {results['failed_count']} sheet(s) failed"

                                    ui.label(summary).classes("whitespace-pre-line")

                                    # Show details in expandable section
                                    if results["details"]:
                                        with ui.expansion("Details", icon="info").classes("w-full"):
                                            for _sheet_name, changed, message in results["details"]:
                                                status_icon = (
                                                    "✓"
                                                    if changed
                                                    else "•"
                                                    if "No changes" in message
                                                    else "✗"
                                                )
                                                ui.label(f"{status_icon} {message}").classes(
                                                    "text-sm"
                                                )

                                # Close button
                                ui.button("Close", on_click=result_dialog.close).props("flat")

                            result_dialog.open()

                        except Exception as e:
                            loading_dialog.close()
                            ui.notify(f"Failed to refresh data: {str(e)}", type="negative")

                    # Refresh Data button with icon
                    refresh_button = ui.button(on_click=refresh_data).classes(
                        "btn bg-secondary hover:bg-secondary/80 text-secondary-content w-full max-w-xs"
                    )
                    with refresh_button:
                        with ui.row().classes("items-center justify-center gap-2"):
                            ui.html(styles.REFRESH_SVG, sanitize=False)
                            ui.label("Refresh Data")

            # ========== About Tab ==========
            with ui.tab_panel(about_tab):
                with ui.column().classes("w-full gap-6"):
                    # Version info
                    ui.label(f"Kanso v{APP_VERSION}").classes("text-xl font-semibold")
                    ui.label("Personal Finance Dashboard").classes("text-base opacity-70")

                    # Resources section
                    ui.separator().classes("my-6")
                    ui.label("Resources").classes("text-xl font-semibold")

                    with ui.column().classes("gap-2"):
                        # Documentation link with icon
                        with ui.link(
                            target="https://dstmrk.github.io/kanso/", new_tab=True
                        ).classes("flex items-center gap-2 text-primary hover:underline"):
                            ui.html(styles.DOCUMENT_SVG, sanitize=False)
                            ui.label("Documentation")

                        # GitHub repository link with icon
                        with ui.link(
                            target="https://github.com/dstmrk/kanso", new_tab=True
                        ).classes("flex items-center gap-2 text-primary hover:underline"):
                            ui.html(styles.GITHUB_SVG, sanitize=False)
                            ui.label("GitHub")

                        # Ko-fi support link with icon
                        with ui.link(target="https://ko-fi.com/dstmrk", new_tab=True).classes(
                            "flex items-center gap-2 text-primary hover:underline"
                        ):
                            ui.html(styles.HEART_SVG, sanitize=False)
                            ui.label("Support")
