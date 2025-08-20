from nicegui import ui, app

from app.ui import header
from app.services import pages

def render():
    net_worth_data = app.storage.user.get('net_worth_data')
    asset_vs_liabilities_data = app.storage.user.get('asset_vs_liabilities_data')

    if not net_worth_data:
        ui.label("No net worth data available").classes('text-red')
        return
    ui.colors(primary='#E0E0E0', secondary='#1C293A', accent='#4FC3F7')
    
    header.header()
    with ui.column().classes('items-center w-full max-w-screen-xl mx-auto'):
        # Back button row (aligned left within centered column)
        with ui.row().classes('w-full px-4 mt-2'):
            # Page title
            ui.label("Net Worth Details Page").classes('text-center text-2xl md:text-4xl font-bold my-2 text-primary')

