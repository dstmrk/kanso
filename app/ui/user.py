from nicegui import ui, app
from app.ui import styles, header, dock
from app.services import pages
from app.core.state_manager import state_manager

def render():
    """Render the user settings page with theme toggle and data refresh."""
    
    def save_theme_preference():
        current_theme: str = app.storage.user.get('theme', 'light')
        new_theme: str = 'dark' if current_theme == 'light' else 'light'
        app.storage.user['theme'] = new_theme
        
        # Update localStorage and DOM immediately
        script: str = f"""
            localStorage.setItem('kanso-theme', '{new_theme}');
            document.documentElement.setAttribute('data-theme', '{new_theme}');
            document.documentElement.style.colorScheme = '{new_theme}';
        """
        ui.run_javascript(script)
        

    def refresh_data():
        """Force refresh of all cached data by clearing the cache."""
        state_manager.invalidate_cache()
        ui.notify('Data cache cleared! Data will be refreshed on next page visit.', type='positive')

    header.render()
    with ui.column().classes('mx-auto items-center gap-6 p-4'):
        # Row 1: Theme label and toggle
        with ui.element('label').classes('flex cursor-pointer gap-2 items-center'):
            ui.html(styles.SUN_SVG)
            toggle = ui.element('input').props('type="checkbox" value="dark"').classes('toggle').on('click', save_theme_preference)
            current_theme: str = app.storage.user.get('theme', 'light')
            if current_theme == 'dark':
                toggle.props('checked')
            ui.html(styles.MOON_SVG)
        
        # Row 2: Data refresh button only
        with ui.element('button').on('click', refresh_data).classes('btn bg-secondary hover:bg-secondary/80 text-secondary-content'):
            ui.label('Refresh Data')
        
        # Row 3: Logout button only
        with ui.element('button').on('click', lambda: ui.navigate.to(pages.LOGOUT_PAGE)).classes('btn btn-outline btn-error'):
            ui.label('Logout')
    
    dock.render()