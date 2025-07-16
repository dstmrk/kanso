# app/ui/dashboard_page.py
from nicegui import ui
from app.ui import charts

def create_page(net_worth_data, theme):
    """Builds the entire dashboard UI."""
    ui.add_head_html('<style>body {background-color: rgba(41,52,65,1); }</style>')
    with ui.column().classes('w-full items-center'):
        with ui.row():
            ui.label("Personal Finance Dashboard").tailwind("text-3xl", "text-gray-200")
        net_worth_options = charts.create_net_worth_chart_options(net_worth_data)
        ui.echart(options=net_worth_options, theme=theme)
