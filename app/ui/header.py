from nicegui import ui

from app.services import pages
from app.ui import styles


def render() -> None:
    """Render the navigation header with hamburger menu."""
    # Always create a new drawer for each page (required for NiceGUI)
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
            profile_picture.on("click", lambda: ui.navigate.to(pages.USER_PAGE))

    # Header mobile
    with ui.header().classes("bg-secondary p-2 md:hidden"):
        with ui.row().classes("w-full justify-center"):
            with ui.row().classes("items-center gap-x-1 cursor-pointer") as title_center:
                ui.label("Kanso").classes("font-semibold text-2xl")
            title_center.props('tabindex="0" role="button" aria-label="Go home"')
            title_center.on("click", lambda: ui.navigate.to(pages.HOME_PAGE))
