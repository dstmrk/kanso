from nicegui import ui, app

PROFILE_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
</svg>
'''

def header():
    with ui.left_drawer().classes('bg-base-100 w-64') as left_drawer:
        ui.link('Dashboard', '/home').classes('p-2')
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
            profile_picture = ui.html(PROFILE_SVG).classes('avatar cursor-pointer')
            profile_picture.on('click', right_drawer.toggle)