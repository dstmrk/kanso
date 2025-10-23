from nicegui import app, ui

from app.core.state_manager import state_manager
from app.services import pages
from app.services.data_loader import refresh_all_data
from app.services.utils import format_timestamp_relative
from app.ui import styles


def render_refresh_button() -> None:
    """Render data refresh button."""

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
                        summary += f"\n• {results['unchanged_count']} sheet(s) unchanged"
                    if results["failed_count"] > 0:
                        summary += f"\n✗ {results['failed_count']} sheet(s) failed"

                    ui.label(summary).classes("whitespace-pre-line")

                    # Show details in expandable section
                    if results["details"]:
                        with ui.expansion("Details", icon="info").classes("w-full"):
                            for _sheet_name, changed, message in results["details"]:
                                status_icon = (
                                    "✓" if changed else "•" if "No changes" in message else "✗"
                                )
                                ui.label(f"{status_icon} {message}").classes("text-sm")

                # Close button
                ui.button("Close", on_click=result_dialog.close).props("flat")

            result_dialog.open()

        except Exception as e:
            loading_dialog.close()
            ui.notify(f"Failed to refresh data: {str(e)}", type="negative")

    with (
        ui.element("button")
        .on("click", refresh_data)
        .classes("btn bg-secondary hover:bg-secondary/80 text-secondary-content w-full")
    ):
        ui.label("Refresh Data")


def render_advanced_settings_button() -> None:
    """Render advanced settings button."""
    with (
        ui.element("button")
        .on("click", lambda: ui.navigate.to(pages.USER_PAGE))
        .classes("btn btn-outline w-full")
    ):
        ui.label("Advanced Settings")


def render_logout_button() -> None:
    """Render logout button."""
    with (
        ui.element("button")
        .on("click", lambda: ui.navigate.to(pages.LOGOUT_PAGE))
        .classes("btn btn-outline btn-error w-full")
    ):
        ui.label("Logout")


def render_last_refresh_timestamp() -> None:
    """Render last data refresh timestamp at the bottom of sidebar with auto-refresh.

    Only shows the timestamp section when data has been loaded at least once.
    """
    # Container that will hold the timestamp UI (or stay empty)
    container = ui.column().classes("w-full mt-auto pt-4")

    # Track if UI has been rendered
    ui_rendered = {"value": False}

    def check_and_render():
        """Check if timestamp exists and render/update UI accordingly."""
        last_refresh = app.storage.user.get("last_data_refresh")

        if not last_refresh:
            # No timestamp yet - keep container empty
            container.clear()
            ui_rendered["value"] = False
            return

        # Timestamp exists - render or update UI
        if not ui_rendered["value"]:
            # First time rendering - create UI structure
            with container:
                ui.separator()
                # Title with clock icon
                with ui.row().classes("items-center gap-1 mt-2"):
                    ui.html(styles.CLOCK_SVG, sanitize=False).classes("text-base-content/70")
                    ui.label("Last Data Refresh").classes(
                        "text-xs font-semibold text-base-content/70"
                    )

                # Single label showing relative time
                container.timestamp_label = ui.label().classes(
                    "text-xs text-base-content/60 italic"
                )

            ui_rendered["value"] = True

        # Update timestamp values
        formatted, relative = format_timestamp_relative(last_refresh)

        # Show relative time, with full datetime in tooltip
        if relative:
            container.timestamp_label.set_text(relative)
            container.timestamp_label.tooltip(formatted)
        else:
            # Fallback if no relative time
            container.timestamp_label.set_text(formatted)
            container.timestamp_label.tooltip("")

    # Initial check
    check_and_render()

    # Auto-refresh every 5 seconds to:
    # 1. Detect when timestamp becomes available (first load)
    # 2. Keep relative time updated ("2 minutes ago" -> "3 minutes ago")
    ui.timer(5.0, check_and_render)


def render() -> None:
    """Render the navigation header with hamburger menu and user settings sidebar."""
    # Left drawer for navigation
    with ui.left_drawer(elevated=True, value=False).classes("bg-base-100") as left_drawer:
        with ui.element("ul").classes("menu w-full"):
            with ui.element("li"):
                with ui.element("a").on("click", lambda: ui.navigate.to(pages.HOME_PAGE)):
                    ui.html(styles.HOME_SVG, sanitize=False)
                    ui.label("Dashboard")
            # with ui.element("li"):
            #     with ui.element("a").on("click", lambda: ui.navigate.to(pages.EXPENSES_PAGE)):
            #         ui.html(styles.EXPENSES_SVG)
            #         ui.label("Expenses")

    # Right drawer for user settings
    with ui.right_drawer(elevated=True, value=False).classes("bg-base-100") as right_drawer:
        with ui.column().classes("w-full h-full p-4 gap-6"):
            # Header
            ui.label("User Settings").classes("text-2xl font-bold")
            ui.separator()

            # Settings content
            render_refresh_button()
            render_advanced_settings_button()
            render_logout_button()

            # Last refresh timestamp at bottom
            render_last_refresh_timestamp()

    # Header desktop
    with ui.header().classes("bg-secondary p-2 mobile-hide"):
        with ui.row().classes("w-full items-center justify-between text-2xl"):
            with ui.row().classes("items-center gap-x-1 cursor-pointer") as title_left:
                ui.label("Kanso").classes("font-semibold text-2xl")
            title_left.props('tabindex="0" role="button" aria-label="Toggle menu"')
            title_left.on("click", left_drawer.toggle)
            profile_picture = ui.html(styles.PROFILE_SVG, sanitize=False).classes(
                "avatar cursor-pointer"
            )
            profile_picture.on("click", right_drawer.toggle)

    # Header mobile
    with ui.header().classes("bg-secondary p-2 md:hidden"):
        with ui.row().classes("w-full justify-center"):
            with ui.row().classes("items-center gap-x-1 cursor-pointer") as title_center:
                ui.label("Kanso").classes("font-semibold text-2xl")
            title_center.props('tabindex="0" role="button" aria-label="Go home"')
            title_center.on("click", lambda: ui.navigate.to(pages.HOME_PAGE))
