from nicegui import ui, app

from app.ui import styles, header, dock
from app.services import utils
from app.logic import finance_calculator

def render():
    data_sheet = app.storage.user.get('data_sheet')
    if data_sheet:
        data_sheet = utils.read_json(data_sheet)
        #net_worth = utils.get_or_store(app.storage.user, 'current_net_worth', lambda: finance_calculator.get_current_net_worth(data_sheet))
        fi_progress = utils.get_or_store(app.storage.user, 'fi_progress', lambda: finance_calculator.get_fi_progress(data_sheet))
    header.render()
    with ui.column().classes('items-center w-full max-w-screen-xl mx-auto'):
        with ui.row().classes('w-full px-4 mt-2'):
            ui.label("Net Worth Details Page").classes('text-center text-2xl md:text-4xl font-bold my-2 text-primary')
            with ui.card().classes(styles.STAT_CARDS_CLASSES):
                    fi_progress_value = '{:.2%}'.format(fi_progress)
                    ui.tooltip('Change vs same month last year').classes('tooltip')
                    ui.label('FI Progress').classes(styles.STAT_CARDS_LABEL_CLASSES)
                    text_color = ''
                    if fi_progress < 0.33:
                        text_color = 'text-error'
                    elif fi_progress < 0.66:
                        text_color = 'text-warning'
                    else:
                        text_color = 'text-success'
                    ui.label(fi_progress_value).classes(text_color + styles.STAT_CARDS_VALUE_CLASSES)
                    ui.label('As of today').classes(styles.STAT_CARDS_DESC_CLASSES)
    dock.render()