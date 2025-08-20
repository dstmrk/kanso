from nicegui import ui, app
from app.services import pages
from app.ui import styles

def header():
    with ui.left_drawer().classes('bg-base-100 w-64') as left_drawer:
        ui.link('Dashboard', pages.HOME_PAGE).classes('p-2')
        ui.link('Accounts', '#').classes('p-2')
        ui.link('Reports', '#').classes('p-2')
        ui.link('Settings', '#').classes('p-2')
                    
    with ui.right_drawer(fixed=False).classes('bg-base-100 w-64') as right_drawer:
        ui.link('Account', '#').classes('p-2')
        ui.link('Logout', '#').classes('p-2')
                    
    left_drawer.hide()
    right_drawer.hide()
    
    with ui.header().classes('bg-secondary p-2 mobile-hide'):
        with ui.row().classes('w-full items-center justify-between text-2xl'):
            title_left = ui.label('Kanso').classes('font-semibold cursor-pointer')
            title_left.props('tabindex="0" role="button" aria-label="Toggle menu"')
            title_left.on('click', left_drawer.toggle)
            profile_picture = ui.html(styles.PROFILE_SVG).classes('avatar cursor-pointer')
            profile_picture.on('click', right_drawer.toggle)