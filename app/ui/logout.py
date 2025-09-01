from nicegui import ui, app
from app.services import pages
from app.ui import styles

def render() -> None:
    ui.label('Bye!').classes('text-2xl')
    with ui.element('button').on('click', lambda: ui.navigate.to(pages.HOME_PAGE)).classes('btn btn-outline'):
        ui.html(styles.HOME_SVG)
        ui.label('Home')