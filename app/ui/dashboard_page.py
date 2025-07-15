# app/ui/dashboard_page.py
from nicegui import ui
from app.ui import charts

def create_page(net_worth_data, theme):
    """Builds the entire dashboard UI."""
    ui.label("Personal Finance Dashboard")
    net_worth_options = charts.create_net_worth_chart_options(net_worth_data)
    ui.echart(options=net_worth_options, theme=theme)