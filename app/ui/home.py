from nicegui import ui, app

from app.ui import charts
from app.services import utils, pages
from app.logic import finance_calculator

FIRST_ROW_CARDS_CLASSES = ' w-full md:w-[23%] flex flex-col items-center justify-center min-w-[200px] bg-secondary h-[15vh] cursor-pointer hover:shadow-lg transition'
FIRST_ROW_CARDS_LABEL_CLASSES = ' text-xl md:text-3xl font-normal'
FIRST_ROW_CARDS_VALUE_CLASSES = ' text-xl md:text-3xl font-bold'

SECOND_ROW_CARDS_CLASSES = ' w-full md:w-[48%] flex flex-col relative overflow-hidden items-center justify-center bg-secondary'
SECOND_ROW_CARDS_LABEL_CLASSES = ' text-xl md:text-3xl font-normal'
SECOND_ROW_CARDS_CHARTS_CLASSES = ' w-full h-[30vh]'

THIRD_ROW_CARDS_CLASSES = ' w-full md:w-[32%] flex flex-col relative overflow-hidden items-center justify-center bg-secondary'
THIRD_ROW_CARDS_LABEL_CLASSES = ' text-xl md:text-3xl font-normal'
THIRD_ROW_CARDS_CHARTS_CLASSES = ' w-full h-[23vh]'

def render():
    data_sheet = app.storage.user.get('data_sheet')
    expenses_sheet = app.storage.user.get('expenses_sheet')
    user_agent = app.storage.client.get("user_agent") or ""
    theme = app.storage.user.get("theme_url") or ""
    if data_sheet and expenses_sheet:
        data_sheet = utils.read_json(data_sheet)
        expenses_sheet = utils.read_json(expenses_sheet)
        net_worth = utils.get_or_store(app.storage.user, 'current_net_worth', lambda: finance_calculator.get_current_net_worth(data_sheet))
        mom_variation = utils.get_or_store(app.storage.user, 'mom_variation', lambda: finance_calculator.get_month_over_month_net_worth_variation(data_sheet))
        avg_saving_ratio = utils.get_or_store(app.storage.user, 'avg_saving_ratio', lambda: finance_calculator.get_average_saving_ratio_last_12_months(data_sheet))
        fi_progress = utils.get_or_store(app.storage.user, 'fi_progress', lambda: finance_calculator.get_fi_progress(data_sheet))
        net_worth_data = utils.get_or_store(app.storage.user, 'net_worth_data', lambda: finance_calculator.get_monthly_net_worth(data_sheet))
        asset_vs_liabilities_data = utils.get_or_store(app.storage.user, 'assets_vs_liabilities_data', lambda: finance_calculator.get_assets_liabilities(data_sheet))
        incomes_vs_expenses_data = utils.get_or_store(app.storage.user, 'incomes_vs_expenses_data', lambda: finance_calculator.get_incomes_vs_expenses(data_sheet))
        cash_flow_data = utils.get_or_store(app.storage.user, 'cash_flow_data', lambda: finance_calculator.get_cash_flow_last_12_months(data_sheet, expenses_sheet))
        avg_expenses = utils.get_or_store(app.storage.user, 'avg_expenses', lambda: finance_calculator.get_average_expenses_by_category_last_12_months(expenses_sheet))
        ui.colors(primary='#E0E0E0', secondary='#1C293A', accent='#4FC3F7')
        with ui.column().classes('items-center w-full max-w-screen-xl mx-auto'):
            ui.label('🔘 ' + pages.TITLE).classes('text-center text-2xl md:text-4xl font-bold my-2 text-primary')

            # --- Row 1: KPI cards ---
            with ui.row().classes('w-full flex justify-between gap-4 px-4 text-primary'):
                net_worth_value = '€ {:.0f}'.format(net_worth)
                mom_variation_value = '{:.2%}'.format(mom_variation)
                avg_saving_ratio_value = '{:.2%}'.format(avg_saving_ratio)
                fi_progress_value = '{:.2%}'.format(fi_progress)
                with ui.card().classes(FIRST_ROW_CARDS_CLASSES).on('click', lambda: ui.navigate.to(pages.NET_WORTH_PAGE)):
                    ui.label('Net Worth').classes(FIRST_ROW_CARDS_LABEL_CLASSES)
                    text_color = ''
                    if net_worth < 0:
                        text_color = 'text-red'
                    ui.label(net_worth_value).classes(text_color + FIRST_ROW_CARDS_VALUE_CLASSES)
                with ui.card().classes(FIRST_ROW_CARDS_CLASSES):
                    ui.label('MoM Δ').classes(FIRST_ROW_CARDS_LABEL_CLASSES)
                    text_color = 'text-green'
                    if mom_variation < 0:
                        text_color = 'text-red'
                    ui.label(mom_variation_value).classes(text_color + FIRST_ROW_CARDS_VALUE_CLASSES)
                with ui.card().classes(FIRST_ROW_CARDS_CLASSES):
                    ui.label('Avg Saving Ratio').classes(FIRST_ROW_CARDS_LABEL_CLASSES)
                    text_color = ''
                    if avg_saving_ratio < 0.1:
                        text_color = 'text-red'
                    elif avg_saving_ratio < 0.3:
                        text_color = 'text-orange'
                    elif avg_saving_ratio < 0.5:
                        text_color = 'text-yellow'
                    else:
                        text_color = 'text-green'
                    ui.label(avg_saving_ratio_value).classes(text_color + FIRST_ROW_CARDS_VALUE_CLASSES)
                with ui.card().classes(FIRST_ROW_CARDS_CLASSES):
                    ui.label('FI Progress').classes(FIRST_ROW_CARDS_LABEL_CLASSES)
                    text_color = ''
                    if fi_progress < 0.3:
                        text_color = 'text-red'
                    elif fi_progress < 0.6:
                        text_color = 'text-orange'
                    elif fi_progress < 0.9:
                        text_color = 'text-yellow'
                    else:
                        text_color = 'text-green'
                    ui.label(fi_progress_value).classes(text_color + FIRST_ROW_CARDS_VALUE_CLASSES)
            # --- Row 2: 2 charts ---
            with ui.row().classes('w-full flex justify-between gap-4 px-4 mt-1 text-primary'):
                with ui.card().classes(SECOND_ROW_CARDS_CLASSES):
                    ui.label('Net Worth').classes(SECOND_ROW_CARDS_LABEL_CLASSES)
                    net_worth_options = charts.create_net_worth_chart_options(net_worth_data, user_agent)
                    ui.echart(options=net_worth_options, theme=theme).classes(SECOND_ROW_CARDS_CHARTS_CLASSES)

                with ui.card().classes(SECOND_ROW_CARDS_CLASSES):
                    ui.label('Asset vs Liabilities').classes(SECOND_ROW_CARDS_LABEL_CLASSES)
                    asset_vs_liabilities_options = charts.create_asset_vs_liabilities_chart(asset_vs_liabilities_data, user_agent)
                    ui.echart(options=asset_vs_liabilities_options, theme=theme).classes(SECOND_ROW_CARDS_CHARTS_CLASSES)

            # --- Row 3: 3 charts ---
            with ui.row().classes('w-full flex justify-between gap-4 px-4 mt-1 text-primary'):
                with ui.card().classes(THIRD_ROW_CARDS_CLASSES):
                        ui.label('Cash Flow').classes(THIRD_ROW_CARDS_LABEL_CLASSES)
                        cash_flow_options = charts.create_cash_flow_options(cash_flow_data, user_agent)
                        ui.echart(options=cash_flow_options, theme=theme).classes(THIRD_ROW_CARDS_CHARTS_CLASSES)
                with ui.card().classes(THIRD_ROW_CARDS_CLASSES):
                        ui.label('Avg Expenses').classes(THIRD_ROW_CARDS_LABEL_CLASSES)
                        expenses_options = charts.create_avg_expenses_options(avg_expenses, user_agent)
                        ui.echart(options=expenses_options, theme=theme).classes(THIRD_ROW_CARDS_CHARTS_CLASSES)
                with ui.card().classes(THIRD_ROW_CARDS_CLASSES):
                        ui.label('Income vs Expenses').classes(THIRD_ROW_CARDS_LABEL_CLASSES)
                        income_vs_expenses_options = charts.create_income_vs_expenses_options(incomes_vs_expenses_data, user_agent)
                        ui.echart(options=income_vs_expenses_options, theme=theme).classes(THIRD_ROW_CARDS_CHARTS_CLASSES)