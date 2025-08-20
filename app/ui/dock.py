from nicegui import ui
from app.services import pages
from app.ui import styles

ITEMS = [
    (pages.HOME_PAGE, 'Home', '''<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6"><path stroke-linecap="round" stroke-linejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" /></svg>'''),
    ('expenses', 'Expenses',  '''<svg xmlns="http://www.w3.org/2000/svg" class="size-[1.2em]" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0ZM3.75 12h.007v.008H3.75V12Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm-.375 5.25h.007v.008H3.75v-.008Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" /></svg>'''),
    ('profile', 'Profile',  styles.PROFILE_SVG),
]

def dock():
    buttons = []
    with ui.row().classes('dock md:hidden fixed bottom-0 left-0 right-0 bg-base-200 z-50'):
        for i, (key, label, svg) in enumerate(ITEMS):
            classes = 'flex-1 flex flex-col items-center justify-center py-2 gap-1 rounded-none'
            if i == 0:  # first button active
                classes += ' dock-active'
            btn = ui.element('button').classes(classes)
            buttons.append(btn)
            with btn.on('click', lambda e, idx=i, k=key: change_tab(idx, k, buttons)):
                ui.html(svg)
                ui.label(label).classes('dock-label')
                
    def change_tab(index, key, buttons):
        # update active class
        for i, btn in enumerate(buttons):
            btn.classes(remove='dock-active')
            if i == index:
                btn.classes('dock-active')
        # trigger notification (or any other logic)
        ui.navigate.to('/'+key)