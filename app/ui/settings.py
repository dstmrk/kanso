import logging

from nicegui import app, ui

from app.core.constants import APP_VERSION, CURRENCY_OPTIONS_SHORT
from app.core.error_messages import ErrorMessages, get_user_message
from app.core.exceptions import KansoError
from app.core.state_manager import state_manager
from app.core.validators import validate_credentials_and_url
from app.services import pages, utils
from app.services.data_loader import refresh_all_data
from app.services.utils import get_user_currency
from app.ui import header, styles
from app.ui.styles import (
    SETTINGS_RESOURCE_LINK_CLASSES,
    SETTINGS_ROW_CLASSES,
    SETTINGS_SECTION_CLASSES,
    SETTINGS_SECTION_TITLE_CLASSES,
)

logger = logging.getLogger(__name__)


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
                with ui.column().classes(SETTINGS_SECTION_CLASSES):
                    # Appearance section
                    ui.label("Appearance").classes(SETTINGS_SECTION_TITLE_CLASSES)

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

                    with ui.row().classes(SETTINGS_ROW_CLASSES):
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
                    ui.label("Account").classes(SETTINGS_SECTION_TITLE_CLASSES)

                    # Logout button
                    with (
                        ui.element("button")
                        .on("click", lambda: ui.navigate.to(pages.LOGOUT_PAGE))
                        .classes("btn btn-outline btn-error w-full max-w-xs")
                    ):
                        ui.label("Logout")

            # ========== Data Tab ==========
            with ui.tab_panel(data_tab):
                with ui.column().classes(SETTINGS_SECTION_CLASSES):
                    # Google Sheets Configuration section
                    ui.label("Google Sheets Configuration").classes(SETTINGS_SECTION_TITLE_CLASSES)

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

                    def save_and_test_configuration():
                        """Validate, save and test both credentials and URL."""
                        # Get values
                        credentials_content = credentials_textarea.value.strip()
                        url_value = url_input.value.strip()

                        # Validate required fields
                        for value, msg in [
                            (credentials_content, "Please paste the credentials JSON"),
                            (url_value, "Please enter a Google Sheet URL"),
                        ]:
                            if not value:
                                ui.notify(f"✗ {msg}", type="negative")
                                return

                        # Validate credentials + URL together
                        is_valid, result, clean_url = validate_credentials_and_url(
                            credentials_content, url_value
                        )
                        if not is_valid:
                            ui.notify(f"✗ {result}", type="negative")
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

                        # Show loading dialog during connection test
                        with ui.dialog() as test_dialog, ui.card().classes(SETTINGS_ROW_CLASSES):
                            ui.label("Testing connection...").classes("text-lg")
                            ui.spinner(
                                size=styles.LOADING_SPINNER_SIZE, color=styles.LOADING_SPINNER_COLOR
                            )

                        test_dialog.open()

                        # Test the connection with cleaned URL
                        try:
                            with utils.temporary_sheet_service(credentials_content, clean_url):
                                test_dialog.close()
                                ui.notify(ErrorMessages.CONFIG_SAVED_AND_VERIFIED, type="positive")
                        except (KansoError, ValueError, RuntimeError) as e:
                            test_dialog.close()
                            logger.warning(f"Connection test failed: {e}")
                            msg = get_user_message(e) if isinstance(e, KansoError) else str(e)
                            ui.notify(
                                f"⚠ Configuration saved, but connection test failed: {msg}",
                                type="warning",
                            )

                    ui.button(
                        "Save & Test Configuration", on_click=save_and_test_configuration
                    ).classes("btn bg-secondary hover:bg-secondary/80 text-secondary-content mt-2")

                    # Data Management section
                    ui.separator().classes("my-6")
                    ui.label("Data Management").classes(SETTINGS_SECTION_TITLE_CLASSES)

                    # Refresh Data button
                    async def refresh_data() -> None:
                        """Force refresh all data from Google Sheets and clear cache."""
                        # Show loading state
                        with ui.dialog() as loading_dialog, ui.card().classes(SETTINGS_ROW_CLASSES):
                            ui.label("Refreshing data from Google Sheets...").classes("text-lg")
                            ui.spinner(
                                size=styles.LOADING_SPINNER_SIZE, color=styles.LOADING_SPINNER_COLOR
                            )

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
                                                if changed:
                                                    status_icon = "✓"
                                                elif "No changes" in message:
                                                    status_icon = "•"
                                                else:
                                                    status_icon = "✗"
                                                ui.label(f"{status_icon} {message}").classes(
                                                    "text-sm"
                                                )

                                # Close button
                                ui.button("Close", on_click=result_dialog.close).props("flat")

                            result_dialog.open()

                        except KansoError as e:
                            loading_dialog.close()
                            logger.error(f"Error during refresh: {e}")
                            ui.notify(get_user_message(e), type="negative")

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
                with ui.column().classes(SETTINGS_SECTION_CLASSES):
                    # Version info
                    ui.label(f"Kanso v{APP_VERSION}").classes(SETTINGS_SECTION_TITLE_CLASSES)
                    ui.label("Personal Finance Dashboard").classes("text-base opacity-70")

                    # Resources section
                    ui.separator().classes("my-6")
                    ui.label("Resources").classes(SETTINGS_SECTION_TITLE_CLASSES)

                    with ui.column().classes("gap-2"):
                        # Documentation link with icon
                        with ui.link(
                            target="https://dstmrk.github.io/kanso/", new_tab=True
                        ).classes(SETTINGS_RESOURCE_LINK_CLASSES):
                            ui.html(styles.DOCUMENT_SVG, sanitize=False)
                            ui.label("Documentation")

                        # GitHub repository link with icon
                        with ui.link(
                            target="https://github.com/dstmrk/kanso", new_tab=True
                        ).classes(SETTINGS_RESOURCE_LINK_CLASSES):
                            ui.html(styles.GITHUB_SVG, sanitize=False)
                            ui.label("GitHub")

                        # Ko-fi support link with icon
                        with ui.link(target="https://ko-fi.com/dstmrk", new_tab=True).classes(
                            "flex items-center gap-2 text-primary hover:underline"
                        ):
                            ui.html(styles.HEART_SVG, sanitize=False)
                            ui.label("Support")
