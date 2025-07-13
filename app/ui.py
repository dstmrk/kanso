from nicegui import ui, app
from app.charts import get_dashboard_data, build_net_worth_chart
from app.utils import load_env

ECHARTS_THEME_PATH_KEY = "ECHARTS_THEME_PATH_URL"

def build_ui():
    data = get_dashboard_data()
    with ui.row():
        ui.label("My Finance Dashboard").classes("text-2xl")
    
    ui.table(rows=data)
    return ui


def build_ui_mock():
    app.add_static_files('/themes', 'static/themes')
    net_worth_chart_data = build_net_worth_chart()
    ui.echart(options=net_worth_chart_data, theme=load_env(ECHARTS_THEME_PATH_KEY))
    return ui