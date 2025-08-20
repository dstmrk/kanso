from nicegui import ui
from app.ui import styles, header, dock


def render():
    """Pagina delle impostazioni utente con il toggle per il tema."""
    header.render()
    with ui.column().classes('mx-auto items-center gap-4'):
        with ui.element('label').classes('flex cursor-pointer gap-2 items-center'):
            ui.html(styles.SUN_SVG)
            ui.element('input').props('type="checkbox" value="dark"').classes('toggle theme-controller')
            ui.html(styles.MOON_SVG)
    dock.render()