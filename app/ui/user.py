from nicegui import ui, app
from app.ui import styles, header, dock
from app.services import pages

def render():
    def save_theme_preference():
        current_theme = app.storage.user.get('theme', 'light')
        new_theme = 'dark' if current_theme == 'light' else 'light'
        app.storage.user['theme'] = new_theme
        ui.run_javascript(f"document.documentElement.setAttribute('data-theme', '{new_theme}')")
        

    header.render()
    with ui.column().classes('mx-auto items-center gap-4'):
        with ui.element('label').classes('flex cursor-pointer gap-2 items-center'):
            ui.html(styles.SUN_SVG)
            toggle = ui.element('input').props('type="checkbox" value="dark"').classes('toggle').on('click', save_theme_preference)
            current_theme = app.storage.user.get('theme', 'light')
            if current_theme == 'dark':
                toggle.props('checked')
            ui.html(styles.MOON_SVG)
        with ui.element('button').on('click', lambda: ui.navigate.to(pages.LOGOUT_PAGE)).classes('btn btn-outline btn-error'):
            ui.label('Logout')
    dock.render()