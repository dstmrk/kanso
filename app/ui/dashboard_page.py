# app/ui/dashboard_page.py
from nicegui import ui
from app.ui import charts

def create_page(net_worth_data, expense_data):
    """Builds the entire dashboard UI."""
    ui.label("Personal Finance Dashboard").classes("text-h4 font-bold text-center my-4")

    with ui.row().classes("w-full justify-center"):
        with ui.card().classes("w-full md:w-2/3"):
            # Use the registered theme name 'my_theme'
            net_worth_options = charts.create_net_worth_chart_options(net_worth_data)
            ui.echart(net_worth_options, theme='my_theme').classes('h-96')