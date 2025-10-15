from nicegui import ui

from app.core.state_manager import state_manager
from app.services import pages
from app.ui import styles


def render_refresh_button() -> None:
    """Render data refresh button."""

    def refresh_data() -> None:
        """Force refresh of all cached data by clearing the cache."""
        state_manager.invalidate_cache()
        ui.notify("Data cache cleared! Data will be refreshed on next page visit.", type="positive")

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
        with ui.column().classes("w-full p-4 gap-6"):
            # Header
            ui.label("User Settings").classes("text-2xl font-bold")
            ui.separator()

            # Settings content
            render_refresh_button()
            render_advanced_settings_button()
            render_logout_button()

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
