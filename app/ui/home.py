from nicegui import ui, app

from app.ui import styles, charts, header, dock
from app.services import utils, pages
from app.logic import finance_calculator

def render():
    data_sheet = app.storage.user.get('data_sheet')
    expenses_sheet = app.storage.user.get('expenses_sheet')
    user_agent = app.storage.client.get("user_agent") or ""
    theme = app.storage.user.get("theme_url") or ""
    if data_sheet and expenses_sheet:
        data_sheet = utils.read_json(data_sheet)
        expenses_sheet = utils.read_json(expenses_sheet)
        last_update_date = utils.get_or_store(app.storage.user, 'last_update_date', lambda: finance_calculator.get_last_update_date(data_sheet))
        net_worth = utils.get_or_store(app.storage.user, 'current_net_worth', lambda: finance_calculator.get_current_net_worth(data_sheet))
        mom_variation_percentage = utils.get_or_store(app.storage.user, 'mom_variation_percentage', lambda: finance_calculator.get_month_over_month_net_worth_variation_percentage(data_sheet))
        mom_variation_absolute = utils.get_or_store(app.storage.user, 'mom_variation_absolute', lambda: finance_calculator.get_month_over_month_net_worth_variation_absolute(data_sheet))
        yoy_variation_percentage = utils.get_or_store(app.storage.user, 'yoy_variation_percentage', lambda: finance_calculator.get_year_over_year_net_worth_variation_percentage(data_sheet))
        yoy_variation_absolute = utils.get_or_store(app.storage.user, 'yoy_variation_absolute', lambda: finance_calculator.get_year_over_year_net_worth_variation_absolute(data_sheet))
        avg_saving_ratio_percentage = utils.get_or_store(app.storage.user, 'avg_saving_ratio_percentage', lambda: finance_calculator.get_average_saving_ratio_last_12_months_percentage(data_sheet))
        avg_saving_ratio_absolute = utils.get_or_store(app.storage.user, 'avg_saving_ratio_absolute', lambda: finance_calculator.get_average_saving_ratio_last_12_months_absolute(data_sheet))
        net_worth_data = utils.get_or_store(app.storage.user, 'net_worth_data', lambda: finance_calculator.get_monthly_net_worth(data_sheet))
        asset_vs_liabilities_data = utils.get_or_store(app.storage.user, 'assets_vs_liabilities_data', lambda: finance_calculator.get_assets_liabilities(data_sheet))
        incomes_vs_expenses_data = utils.get_or_store(app.storage.user, 'incomes_vs_expenses_data', lambda: finance_calculator.get_incomes_vs_expenses(data_sheet))
        cash_flow_data = utils.get_or_store(app.storage.user, 'cash_flow_data', lambda: finance_calculator.get_cash_flow_last_12_months(data_sheet, expenses_sheet))
        avg_expenses = utils.get_or_store(app.storage.user, 'avg_expenses', lambda: finance_calculator.get_average_expenses_by_category_last_12_months(expenses_sheet))
        
        header.render()
        
        with ui.column().classes('w-full max-w-screen-xl mx-auto p-4 space-y-5 main-content'):

            # --- Row 1: KPI cards ---
            with ui.row().classes('grid grid-cols-1 md:grid-cols-4 gap-4 w-full'):
                net_worth_value = '€ {:.0f}'.format(net_worth)
                mom_variation_percentage_value = '{:.2%}'.format(mom_variation_percentage)
                mom_variation_absolute_value = '{:.0f}€'.format(mom_variation_absolute)
                yoy_variation_percentage_value = '{:.2%}'.format(yoy_variation_percentage)
                yoy_variation_absolute_value = '{:.0f}€'.format(yoy_variation_absolute)
                avg_saving_ratio_percentage_value = '{:.2%}'.format(avg_saving_ratio_percentage)
                avg_saving_ratio_absolute_value = '{:.0f}€'.format(avg_saving_ratio_absolute)
                with ui.card().classes('cursor-pointer' + styles.STAT_CARDS_CLASSES).on('click', lambda: ui.navigate.to(pages.NET_WORTH_PAGE)):
                    ui.label('Net Worth').classes(styles.STAT_CARDS_LABEL_CLASSES)
                    ui.label(net_worth_value).classes(styles.STAT_CARDS_VALUE_CLASSES)
                    ui.label('As of ' + last_update_date).classes(styles.STAT_CARDS_DESC_CLASSES)
                with ui.card().classes(styles.STAT_CARDS_CLASSES):
                    ui.tooltip('Change vs previous month').classes('tooltip')
                    ui.label('MoM Δ').classes(styles.STAT_CARDS_LABEL_CLASSES)
                    sign = '+'
                    text_color = 'text-success'
                    if mom_variation_percentage < 0:
                        text_color = 'text-error'
                        sign = '-'
                    ui.label(sign + mom_variation_percentage_value).classes(text_color + styles.STAT_CARDS_VALUE_CLASSES)
                    ui.label(sign + mom_variation_absolute_value + ' compared to last month').classes(styles.STAT_CARDS_DESC_CLASSES)
                with ui.card().classes(styles.STAT_CARDS_CLASSES):
                    ui.tooltip('Change vs same month last year').classes('tooltip')
                    ui.label('YoY Δ').classes(styles.STAT_CARDS_LABEL_CLASSES)
                    sign = '+'
                    text_color = 'text-success'
                    if yoy_variation_percentage < 0:
                        text_color = 'text-error'
                        sign = '-'
                    ui.label(sign + yoy_variation_percentage_value).classes(text_color + styles.STAT_CARDS_VALUE_CLASSES)
                    ui.label(sign + yoy_variation_absolute_value + ' compared to last year').classes(styles.STAT_CARDS_DESC_CLASSES)
                with ui.card().classes(styles.STAT_CARDS_CLASSES):
                    ui.tooltip('Average monthly Saving Ratio of last 12 months').classes('tooltip')
                    ui.label('Avg Saving Ratio').classes(styles.STAT_CARDS_LABEL_CLASSES)
                    text_color = ''
                    if avg_saving_ratio_percentage < 0.2:
                        text_color = 'text-error'
                    elif avg_saving_ratio_percentage < 0.4:
                        text_color = 'text-warning'
                    else:
                        text_color = 'text-success'
                    ui.label(avg_saving_ratio_percentage_value).classes(text_color + styles.STAT_CARDS_VALUE_CLASSES)
                    ui.label(avg_saving_ratio_absolute_value + ' saved on average each month').classes(styles.STAT_CARDS_DESC_CLASSES)
            # --- Row 2: 2 charts ---
            with ui.row().classes('grid grid-cols-1 lg:grid-cols-2 gap-4 w-full'):
                with ui.card().classes(styles.CHART_CARDS_CLASSES):
                    ui.label('Net Worth').classes(styles.CHART_CARDS_LABEL_CLASSES)
                    net_worth_options = charts.create_net_worth_chart_options(net_worth_data, user_agent)
                    ui.echart(options=net_worth_options, theme=theme).classes(styles.CHART_CARDS_CHARTS_CLASSES)

                with ui.card().classes(styles.CHART_CARDS_CLASSES):
                    ui.label('Asset vs Liabilities').classes(styles.CHART_CARDS_LABEL_CLASSES)
                    asset_vs_liabilities_options = charts.create_asset_vs_liabilities_chart(asset_vs_liabilities_data, user_agent)
                    ui.echart(options=asset_vs_liabilities_options, theme=theme).classes(styles.CHART_CARDS_CHARTS_CLASSES)

            # --- Row 3: 3 charts ---
            with ui.row().classes('grid grid-cols-1 lg:grid-cols-3 gap-4 w-full'):
                with ui.card().classes(styles.CHART_CARDS_CLASSES):
                        ui.label('Cash Flow').classes(styles.CHART_CARDS_LABEL_CLASSES)
                        cash_flow_options = charts.create_cash_flow_options(cash_flow_data, user_agent)
                        ui.echart(options=cash_flow_options, theme=theme).classes(styles.CHART_CARDS_CHARTS_CLASSES)
                with ui.card().classes(styles.CHART_CARDS_CLASSES):
                        ui.label('Avg Expenses').classes(styles.CHART_CARDS_LABEL_CLASSES)
                        expenses_options = charts.create_avg_expenses_options(avg_expenses, user_agent)
                        ui.echart(options=expenses_options, theme=theme).classes(styles.CHART_CARDS_CHARTS_CLASSES)
                with ui.card().classes(styles.CHART_CARDS_CLASSES):
                        ui.label('Income vs Expenses').classes(styles.CHART_CARDS_LABEL_CLASSES)
                        income_vs_expenses_options = charts.create_income_vs_expenses_options(incomes_vs_expenses_data, user_agent)
                        ui.echart(options=income_vs_expenses_options, theme=theme).classes(styles.CHART_CARDS_CHARTS_CLASSES)
        dock.render()