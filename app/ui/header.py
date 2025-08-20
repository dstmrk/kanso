from nicegui import ui, app
from app.services import pages
from app.ui import styles

def render():
    #ui.add_head_html("""
#<script>document.documentElement.setAttribute("data-theme",'"""+app.storage.user.get('theme', 'light')+"""');</script>""")
    with ui.left_drawer(elevated=True, value=False).classes('bg-base-100') as left_drawer:
        with ui.element('ul').classes('menu w-full'):
            with ui.element('li'):
                with ui.element('a').props('href='+pages.HOME_PAGE):
                    ui.html(styles.HOME_SVG)
                    ui.label('Dashboard')
            with ui.element('li'):
                with ui.element('a').props('href='+pages.EXPENSES_PAGE):
                    ui.html(styles.EXPENSES_SVG)
                    ui.label('Expenses')
    
    with ui.header().classes('bg-secondary p-2 mobile-hide'):
        with ui.row().classes('w-full items-center justify-between text-2xl'):
            with ui.row().classes('items-center gap-x-1 cursor-pointer') as title_left:
                ui.label('Kanso').classes('font-semibold text-2xl')
            title_left.props('tabindex="0" role="button" aria-label="Toggle menu"')
            title_left.on('click', left_drawer.toggle)
            profile_picture = ui.html(styles.PROFILE_SVG).classes('avatar cursor-pointer')
            profile_picture.on('click', lambda: ui.navigate.to(pages.USER_PAGE))
            
    with ui.header().classes('bg-secondary p-2 md:hidden'):
        with ui.row().classes('w-full justify-center'):
            with ui.row().classes('items-center gap-x-1 cursor-pointer') as title_left:
                ui.label('Kanso').classes('font-semibold text-2xl')
            title_left.props('tabindex="0" role="button" aria-label="Toggle menu"')
            title_left.on('click', lambda: ui.navigate.to(pages.HOME_PAGE))