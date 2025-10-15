from nicegui import app, ui

from app.services import pages
from app.ui import styles

ITEMS = [
    (pages.HOME_PAGE, "Home", styles.HOME_SVG),
    (pages.EXPENSES_PAGE, "Expenses", styles.EXPENSES_SVG),
    (pages.USER_PAGE, "Profile", styles.PROFILE_SVG),
]


def render() -> None:
    active_tab = app.storage.user.get("active_tab", pages.HOME_PAGE)
    buttons: list = []
    with ui.row().classes("dock md:hidden fixed bottom-0 left-0 right-0 bg-base-200 z-50"):
        for i, (key, label, svg) in enumerate(ITEMS):
            classes = "flex-1 flex flex-col items-center justify-center py-2 gap-1 rounded-none"
            if key == active_tab:  # first button active
                classes += " dock-active"
            btn = ui.element("button").classes(classes)
            buttons.append(btn)
            with btn.on("click", lambda _=None, idx=i, k=key: change_tab(idx, k, buttons)):
                ui.html(svg, sanitize=False)
                ui.label(label).classes("dock-label")

    def change_tab(index, key, buttons):
        for i, btn in enumerate(buttons):
            btn.classes(remove="dock-active")
            if i == index:
                btn.classes("dock-active")
                app.storage.user["active_tab"] = key
        ui.navigate.to(key)
