import asyncio
from nicegui import ui, app

from app.ui import styles, charts, header, dock
from app.services import utils, pages
from app.logic import finance_calculator

async def load_kpi_data():
    data_sheet = app.storage.user.get('data_sheet')
    if not data_sheet:
        return None
    
    data_sheet = utils.read_json(data_sheet)
    
    last_update_date = utils.get_or_store(app.storage.user, 'last_update_date', lambda: finance_calculator.get_last_update_date(data_sheet))
    net_worth = utils.get_or_store(app.storage.user, 'current_net_worth', lambda: finance_calculator.get_current_net_worth(data_sheet))
    mom_variation_percentage = utils.get_or_store(app.storage.user, 'mom_variation_percentage', lambda: finance_calculator.get_month_over_month_net_worth_variation_percentage(data_sheet))
    mom_variation_absolute = utils.get_or_store(app.storage.user, 'mom_variation_absolute', lambda: finance_calculator.get_month_over_month_net_worth_variation_absolute(data_sheet))
    yoy_variation_percentage = utils.get_or_store(app.storage.user, 'yoy_variation_percentage', lambda: finance_calculator.get_year_over_year_net_worth_variation_percentage(data_sheet))
    yoy_variation_absolute = utils.get_or_store(app.storage.user, 'yoy_variation_absolute', lambda: finance_calculator.get_year_over_year_net_worth_variation_absolute(data_sheet))
    avg_saving_ratio_percentage = utils.get_or_store(app.storage.user, 'avg_saving_ratio_percentage', lambda: finance_calculator.get_average_saving_ratio_last_12_months_percentage(data_sheet))
    avg_saving_ratio_absolute = utils.get_or_store(app.storage.user, 'avg_saving_ratio_absolute', lambda: finance_calculator.get_average_saving_ratio_last_12_months_absolute(data_sheet))
    
    return {
        'last_update_date': last_update_date,
        'net_worth': net_worth,
        'mom_variation_percentage': mom_variation_percentage,
        'mom_variation_absolute': mom_variation_absolute,
        'yoy_variation_percentage': yoy_variation_percentage,
        'yoy_variation_absolute': yoy_variation_absolute,
        'avg_saving_ratio_percentage': avg_saving_ratio_percentage,
        'avg_saving_ratio_absolute': avg_saving_ratio_absolute
    }

async def load_chart_data():
    data_sheet = app.storage.user.get('data_sheet')
    expenses_sheet = app.storage.user.get('expenses_sheet')
    
    if not data_sheet or not expenses_sheet:
        return None
    
    data_sheet = utils.read_json(data_sheet)
    expenses_sheet = utils.read_json(expenses_sheet)
    
    net_worth_data = utils.get_or_store(app.storage.user, 'net_worth_data', lambda: finance_calculator.get_monthly_net_worth(data_sheet))
    asset_vs_liabilities_data = utils.get_or_store(app.storage.user, 'assets_vs_liabilities_data', lambda: finance_calculator.get_assets_liabilities(data_sheet))
    incomes_vs_expenses_data = utils.get_or_store(app.storage.user, 'incomes_vs_expenses_data', lambda: finance_calculator.get_incomes_vs_expenses(data_sheet))
    cash_flow_data = utils.get_or_store(app.storage.user, 'cash_flow_data', lambda: finance_calculator.get_cash_flow_last_12_months(data_sheet, expenses_sheet))
    avg_expenses = utils.get_or_store(app.storage.user, 'avg_expenses', lambda: finance_calculator.get_average_expenses_by_category_last_12_months(expenses_sheet))
    
    return {
        'net_worth_data': net_worth_data,
        'asset_vs_liabilities_data': asset_vs_liabilities_data,
        'incomes_vs_expenses_data': incomes_vs_expenses_data,
        'cash_flow_data': cash_flow_data,
        'avg_expenses': avg_expenses
    }


def render():
    data_sheet = app.storage.user.get('data_sheet')
    expenses_sheet = app.storage.user.get('expenses_sheet')
    
    header.render()
    
    if not data_sheet or not expenses_sheet:
        with ui.column().classes('w-full max-w-screen-xl mx-auto p-4 space-y-5 main-content'):
            ui.label('No data available. Please upload your data files.').classes('text-center text-gray-500 text-lg')
        dock.render()
        return
    
    with ui.column().classes('w-full max-w-screen-xl mx-auto p-4 space-y-5 main-content'):
        # --- Row 1: KPI cards container ---
        kpi_container = ui.row().classes('grid grid-cols-1 md:grid-cols-4 gap-4 w-full')
        
        # --- Row 2: 2 charts containers ---
        with ui.row().classes('grid grid-cols-1 lg:grid-cols-2 gap-4 w-full'):
            chart1_container = ui.card().classes(styles.CHART_CARDS_CLASSES)
            chart2_container = ui.card().classes(styles.CHART_CARDS_CLASSES)
        
        # --- Row 3: 3 charts containers ---
        with ui.row().classes('grid grid-cols-1 lg:grid-cols-3 gap-4 w-full'):
            chart3_container = ui.card().classes(styles.CHART_CARDS_CLASSES)
            chart4_container = ui.card().classes(styles.CHART_CARDS_CLASSES)
            chart5_container = ui.card().classes(styles.CHART_CARDS_CLASSES)
    
    # Initialize containers with spinners immediately
    with kpi_container:
        with ui.spinner(size='lg', color='primary').classes('w-full h-32 flex items-center justify-center'):
            pass
    
    with chart1_container:
        with ui.spinner(size='lg', color='primary').classes('w-full h-32 flex items-center justify-center'):
            pass
    
    with chart2_container:
        with ui.spinner(size='lg', color='primary').classes('w-full h-32 flex items-center justify-center'):
            pass
    
    with chart3_container:
        with ui.spinner(size='lg', color='primary').classes('w-full h-32 flex items-center justify-center'):
            pass
    
    with chart4_container:
        with ui.spinner(size='lg', color='primary').classes('w-full h-32 flex items-center justify-center'):
            pass
    
    with chart5_container:
        with ui.spinner(size='lg', color='primary').classes('w-full h-32 flex items-center justify-center'):
            pass
    
    # Start loading components with individual timers
    def load_kpi_cards():
        async def load():
            kpi_data = await load_kpi_data()
            kpi_container.clear()
            
            if not kpi_data:
                with kpi_container:
                    ui.label('No data available').classes('text-center text-gray-500')
                return
            
            with kpi_container:
                net_worth_value = '€ {:.0f}'.format(kpi_data['net_worth'])
                mom_variation_percentage_value = '{:.2%}'.format(kpi_data['mom_variation_percentage'])
                mom_variation_absolute_value = '{:.0f}€'.format(kpi_data['mom_variation_absolute'])
                yoy_variation_percentage_value = '{:.2%}'.format(kpi_data['yoy_variation_percentage'])
                yoy_variation_absolute_value = '{:.0f}€'.format(kpi_data['yoy_variation_absolute'])
                avg_saving_ratio_percentage_value = '{:.2%}'.format(kpi_data['avg_saving_ratio_percentage'])
                avg_saving_ratio_absolute_value = '{:.0f}€'.format(kpi_data['avg_saving_ratio_absolute'])
                
                with ui.card().classes('cursor-pointer' + styles.STAT_CARDS_CLASSES).on('click', lambda: ui.navigate.to(pages.NET_WORTH_PAGE)):
                    ui.label('Net Worth').classes(styles.STAT_CARDS_LABEL_CLASSES)
                    ui.label(net_worth_value).classes(styles.STAT_CARDS_VALUE_CLASSES)
                    ui.label('As of ' + kpi_data['last_update_date']).classes(styles.STAT_CARDS_DESC_CLASSES)
                with ui.card().classes(styles.STAT_CARDS_CLASSES):
                    ui.tooltip('Change vs previous month').classes('tooltip')
                    ui.label('MoM Δ').classes(styles.STAT_CARDS_LABEL_CLASSES)
                    sign = '+'
                    text_color = 'text-success'
                    if kpi_data['mom_variation_percentage'] < 0:
                        text_color = 'text-error'
                        sign = '-'
                    ui.label(sign + mom_variation_percentage_value).classes(text_color + styles.STAT_CARDS_VALUE_CLASSES)
                    ui.label(sign + mom_variation_absolute_value + ' compared to last month').classes(styles.STAT_CARDS_DESC_CLASSES)
                with ui.card().classes(styles.STAT_CARDS_CLASSES):
                    ui.tooltip('Change vs same month last year').classes('tooltip')
                    ui.label('YoY Δ').classes(styles.STAT_CARDS_LABEL_CLASSES)
                    sign = '+'
                    text_color = 'text-success'
                    if kpi_data['yoy_variation_percentage'] < 0:
                        text_color = 'text-error'
                        sign = '-'
                    ui.label(sign + yoy_variation_percentage_value).classes(text_color + styles.STAT_CARDS_VALUE_CLASSES)
                    ui.label(sign + yoy_variation_absolute_value + ' compared to last year').classes(styles.STAT_CARDS_DESC_CLASSES)
                with ui.card().classes(styles.STAT_CARDS_CLASSES):
                    ui.tooltip('Average monthly Saving Ratio of last 12 months').classes('tooltip')
                    ui.label('Avg Saving Ratio').classes(styles.STAT_CARDS_LABEL_CLASSES)
                    text_color = ''
                    if kpi_data['avg_saving_ratio_percentage'] < 0.2:
                        text_color = 'text-error'
                    elif kpi_data['avg_saving_ratio_percentage'] < 0.4:
                        text_color = 'text-warning'
                    else:
                        text_color = 'text-success'
                    ui.label(avg_saving_ratio_percentage_value).classes(text_color + styles.STAT_CARDS_VALUE_CLASSES)
                    ui.label(avg_saving_ratio_absolute_value + ' saved on average each month').classes(styles.STAT_CARDS_DESC_CLASSES)
        
        ui.timer(0.1, load, once=True)
    
    def load_chart(container, chart_type, title):
        async def load():
            chart_data = await load_chart_data()
            container.clear()
            
            if not chart_data:
                with container:
                    ui.label(title).classes(styles.CHART_CARDS_LABEL_CLASSES)
                    ui.label('No data available').classes('text-center text-gray-500')
                return
            
            user_agent = app.storage.client.get("user_agent") or ""
            echart_theme = app.storage.user.get("echarts_theme_url") or ""
            
            with container:
                ui.label(title).classes(styles.CHART_CARDS_LABEL_CLASSES)
                
                if chart_type == 'net_worth':
                    options = charts.create_net_worth_chart_options(chart_data['net_worth_data'], user_agent)
                elif chart_type == 'asset_vs_liabilities':
                    options = charts.create_asset_vs_liabilities_chart(chart_data['asset_vs_liabilities_data'], user_agent)
                elif chart_type == 'cash_flow':
                    options = charts.create_cash_flow_options(chart_data['cash_flow_data'], user_agent)
                elif chart_type == 'avg_expenses':
                    options = charts.create_avg_expenses_options(chart_data['avg_expenses'], user_agent)
                elif chart_type == 'income_vs_expenses':
                    options = charts.create_income_vs_expenses_options(chart_data['incomes_vs_expenses_data'], user_agent)
                
                ui.echart(options=options, theme=echart_theme).classes(styles.CHART_CARDS_CHARTS_CLASSES)
        
        ui.timer(0.1, load, once=True)
    
    # Start loading all components
    load_kpi_cards()
    load_chart(chart1_container, 'net_worth', 'Net Worth')
    load_chart(chart2_container, 'asset_vs_liabilities', 'Asset vs Liabilities')  
    load_chart(chart3_container, 'cash_flow', 'Cash Flow')
    load_chart(chart4_container, 'avg_expenses', 'Avg Expenses')
    load_chart(chart5_container, 'income_vs_expenses', 'Income vs Expenses')
    
    dock.render()