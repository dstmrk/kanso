from nicegui import ui
from app.services import pages
from app.ui import styles

ITEMS = [
    (pages.HOME_PAGE, 'Home', styles.HOME_SVG),
    (pages.EXPENSES_PAGE, 'Expenses',  styles.EXPENSES_SVG),
    (pages.USER_PAGE, 'Profile',  styles.PROFILE_SVG),
]

active = pages.HOME_PAGE

def render():
    global active
    buttons = []
    with ui.row().classes('dock md:hidden fixed bottom-0 left-0 right-0 bg-base-200 z-50'):
        for i, (key, label, svg) in enumerate(ITEMS):
            classes = 'flex-1 flex flex-col items-center justify-center py-2 gap-1 rounded-none'
            if key == active:  # first button active
                classes += ' dock-active' 
            btn = ui.element('button').classes(classes)
            buttons.append(btn)
            with btn.on('click', lambda idx=i, k=key: change_tab(idx, k, buttons)):
                ui.html(svg)
                ui.label(label).classes('dock-label')
                
def change_tab(index, key, buttons):
    global active
    for i, btn in enumerate(buttons):
        btn.classes(remove='dock-active')
        if i == index:
            btn.classes('dock-active')
            active = key
    ui.navigate.to(key)