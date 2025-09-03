from nicegui import ui, app

from app.ui import styles, header, dock
from app.services import utils
from app.logic.finance_calculator import FinanceCalculator
import pandas as pd

def render():
    data_sheet_str = app.storage.user.get('data_sheet')
    
    header.render()
    
    with ui.column().classes('items-center w-full max-w-screen-xl mx-auto'):
        with ui.row().classes('w-full px-4 mt-2'):
            ui.label("Net Worth Details Page").classes('text-center text-2xl md:text-4xl font-bold my-2 text-primary')
            
            if data_sheet_str:
                data_sheet = utils.read_json(data_sheet_str)
                calculator = FinanceCalculator(data_sheet)
                fi_progress = calculator.get_fi_progress()
                
                with ui.card().classes(styles.STAT_CARDS_CLASSES):
                    fi_progress_value = '{:.2%}'.format(fi_progress)
                    ui.tooltip('Financial Independence Progress').classes('tooltip')
                    ui.label('FI Progress').classes(styles.STAT_CARDS_LABEL_CLASSES)
                    
                    if fi_progress < 0.33:
                        text_color = 'text-error'
                    elif fi_progress < 0.66:
                        text_color = 'text-warning'
                    else:
                        text_color = 'text-success'
                        
                    ui.label(fi_progress_value).classes(text_color + styles.STAT_CARDS_VALUE_CLASSES)
                    ui.label('As of today').classes(styles.STAT_CARDS_DESC_CLASSES)
            else:
                ui.label('No data available').classes('text-center text-gray-500')
    
    dock.render()