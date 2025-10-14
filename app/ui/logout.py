"""Logout page with session cleanup confirmation."""

from nicegui import ui

from app.services import pages
from app.ui import styles


def render() -> None:
    """Render logout confirmation page with centered content."""
    # Center content vertically and horizontally
    with ui.column().classes("w-full h-screen items-center justify-center gap-6"):
        # Emoji/Icon
        ui.label("👋").classes("text-6xl")

        # Main message
        ui.label("See you soon!").classes("text-3xl font-semibold")

        # Informative text
        with ui.column().classes("items-center gap-2 text-center"):
            ui.label("Your session has been cleared").classes("text-base opacity-70")
            ui.label("All cached data has been removed").classes("text-sm opacity-60")

        # Divider
        ui.separator().classes("w-48")

        # Action button
        with (
            ui.element("button")
            .on("click", lambda: ui.navigate.to(pages.HOME_PAGE))
            .classes("btn bg-secondary hover:bg-secondary/80 text-secondary-content gap-2 mt-4")
        ):
            ui.html(styles.HOME_SVG)
            ui.label("Back to Home")
