from nicegui import app, ui

from app.services import pages
from app.services.utils import format_timestamp_relative
from app.ui import styles
from app.ui.styles import HEADER_BUTTON_PROPS


def render_last_refresh_timestamp() -> None:
    """Render last data refresh timestamp at the bottom of sidebar with auto-refresh.

    Only shows the timestamp section when data has been loaded at least once.
    """
    # Container that will hold the timestamp UI (or stay empty) - compact spacing
    container = ui.column().classes("w-full mt-auto pt-2")

    # Track if UI has been rendered
    ui_rendered = {"value": False}

    def check_and_render():
        """Check if timestamp exists and render/update UI accordingly."""
        last_refresh = app.storage.general.get("last_data_refresh")

        if not last_refresh:
            # No timestamp yet - keep container empty
            container.clear()
            ui_rendered["value"] = False
            return

        # Timestamp exists - render or update UI
        if not ui_rendered["value"]:
            # First time rendering - create UI structure
            with container:
                ui.separator().classes("mb-1")
                # Title with clock icon - compact
                with ui.row().classes("items-center gap-1 mt-1"):
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
        try:
            if relative:
                container.timestamp_label.set_text(relative)
                # Only update tooltip if it doesn't exist yet or text changed
                if (
                    not hasattr(container.timestamp_label, "_tooltip_text")
                    or container.timestamp_label._tooltip_text != formatted
                ):
                    container.timestamp_label.tooltip(formatted)
                    container.timestamp_label._tooltip_text = formatted
            else:
                # Fallback if no relative time
                container.timestamp_label.set_text(formatted)
                if (
                    not hasattr(container.timestamp_label, "_tooltip_text")
                    or container.timestamp_label._tooltip_text != ""
                ):
                    container.timestamp_label.tooltip("")
                    container.timestamp_label._tooltip_text = ""
        except Exception:
            # Client has been disconnected, timer will be cleaned up automatically
            pass

    # Initial check
    check_and_render()

    # Auto-refresh every 5 seconds to:
    # 1. Detect when timestamp becomes available (first load)
    # 2. Keep relative time updated ("2 minutes ago" -> "3 minutes ago")
    ui.timer(5.0, check_and_render)


def render() -> None:
    """Render the navigation header with hamburger menu and consolidated left drawer."""
    # Left drawer for navigation
    with ui.left_drawer(elevated=True, value=False).classes("bg-base-100") as left_drawer:
        with ui.column().classes("w-full h-full"):
            # Navigation menu
            with ui.element("ul").classes("menu w-full"):
                # Dashboard - main entry point
                with ui.element("li"):
                    with ui.element("a").on("click", lambda: ui.navigate.to(pages.HOME_PAGE)):
                        ui.html(styles.HOME_SVG, sanitize=False)
                        ui.label("Dashboard")

                # Insights - collapsible section with detail pages
                with ui.element("li"):
                    with ui.element("details"):
                        with ui.element("summary"):
                            ui.html(styles.INSIGHTS_SVG, sanitize=False)
                            ui.label("Insights")
                        with ui.element("ul"):
                            with ui.element("li"):
                                with ui.element("a").on(
                                    "click", lambda: ui.navigate.to(pages.NET_WORTH_PAGE)
                                ):
                                    ui.html(styles.NET_WORTH_SVG, sanitize=False)
                                    ui.label("Net Worth")
                            with ui.element("li"):
                                with ui.element("a").on(
                                    "click", lambda: ui.navigate.to(pages.EXPENSES_PAGE)
                                ):
                                    ui.html(styles.EXPENSES_SVG, sanitize=False)
                                    ui.label("Expenses")

            # Spacer to push settings and timestamp to bottom
            ui.space()

            # Settings link at bottom (before timestamp) - compact spacing
            with ui.column().classes("w-full px-2 pb-2"):
                ui.separator().classes("mb-2")
                with ui.element("ul").classes("menu w-full p-0"):
                    with ui.element("li"):
                        with ui.element("a").on(
                            "click", lambda: ui.navigate.to(pages.SETTINGS_PAGE)
                        ):
                            ui.html(styles.SETTINGS_SVG, sanitize=False)
                            ui.label("Settings")

                # Last refresh timestamp at very bottom
                render_last_refresh_timestamp()

    # Header desktop
    with ui.header().classes("bg-secondary p-2 mobile-hide"):
        with ui.row().classes("w-full items-center gap-4"):
            # Hamburger menu icon (toggle drawer)
            hamburger = ui.button(icon="menu").props(HEADER_BUTTON_PROPS)
            hamburger.on("click", left_drawer.toggle)

            # Logo Kanso (clickable to go home)
            with ui.link(target=pages.HOME_PAGE).classes("no-underline"):
                ui.html(styles.LOGO_SVG, sanitize=False)

            # Spacer to push Add button to the right
            ui.space()

            # Quick add expense button (desktop: icon + text)
            with ui.link(target="/quick-add").classes("no-underline"):
                with ui.button().props(HEADER_BUTTON_PROPS):
                    ui.html(styles.ADD_SVG, sanitize=False)
                    ui.label("Add").classes("ml-1")
                ui.tooltip("Add Expense")

    # Header mobile
    with ui.header().classes("bg-secondary p-2 md:hidden"):
        with ui.row().classes("w-full items-center relative"):
            # Hamburger menu icon (toggle drawer) - left side
            hamburger = ui.button(icon="menu").props(HEADER_BUTTON_PROPS)
            hamburger.on("click", left_drawer.toggle)

            # Logo Kanso (clickable to go home) - absolutely centered
            with ui.element("div").classes("absolute left-1/2 -translate-x-1/2"):
                with ui.link(target=pages.HOME_PAGE).classes("no-underline"):
                    ui.html(styles.LOGO_SVG, sanitize=False)

            # Spacer to push Add button to the right
            ui.space()

            # Quick add expense button (mobile: icon only)
            with ui.link(target="/quick-add").classes("no-underline"):
                with ui.button().props(HEADER_BUTTON_PROPS):
                    ui.html(styles.ADD_SVG, sanitize=False)
                ui.tooltip("Add Expense")
