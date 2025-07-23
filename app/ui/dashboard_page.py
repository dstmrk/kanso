
from typing import Dict, List, Any
from nicegui import ui, app
from app.ui import charts

def create_page(net_worth_data: Dict[str, Any], asset_vs_liabilities_data: Dict[str, Dict[str, float]], income_vs_expenses_data: Dict[str,List], cash_flow_data: Dict[str, float], avg_expenses: Dict[str, float], net_worth: float, mom_variation: float, avg_saving_ratio: float, fi_progress: float, theme: str, user_agent: str):
    ui.add_head_html('<style>body {background-color: #293441; }</style>')
    ui.colors(primary='#E0E0E0', secondary='#293441', accent='#88B04B')
    
    with ui.column().classes('items-center w-full max-w-screen-xl mx-auto'):
        ui.label('Personal Finance Dashboard').classes('text-center text-2xl md:text-4xl font-bold my-2 text-primary')

        # --- Row 1: KPI cards ---
        with ui.row().classes('w-full flex justify-between gap-4 px-4 text-primary'):
            net_worth_value = '€ {:.0f}'.format(net_worth)
            mom_variation_value = '{:.2%}'.format(mom_variation)
            avg_saving_ratio_value = '{:.2%}'.format(avg_saving_ratio)
            fi_progress_value = '{:.2%}'.format(fi_progress)
            with ui.card().classes('w-full md:w-[23%] flex flex-col items-center justify-center min-w-[200px] bg-secondary h-[15vh]'):
                ui.label('Net Worth').classes('text-xl md:text-3xl font-normal')
                text_color = ''
                if net_worth < 0:
                    text_color = 'text-red'
                ui.label(net_worth_value).classes(f'{text_color} text-xl md:text-3xl font-bold')
            with ui.card().classes('w-full md:w-[23%] flex flex-col items-center justify-center min-w-[200px] bg-secondary h-[15vh]'):
                ui.label('MoM Δ').classes('text-xl md:text-3xl font-normal')
                text_color = 'text-green'
                if mom_variation < 0:
                    text_color = 'text-red'
                ui.label(mom_variation_value).classes(f'{text_color} text-xl md:text-3xl font-bold')
            with ui.card().classes('w-full md:w-[23%] flex flex-col items-center justify-center min-w-[200px] bg-secondary h-[15vh]'):
                ui.label('Avg Saving Ratio').classes('text-xl md:text-3xl font-normal')
                text_color = ''
                if avg_saving_ratio < 0.1:
                    text_color = 'text-red'
                elif avg_saving_ratio < 0.3:
                    text_color = 'text-orange'
                elif avg_saving_ratio < 0.5:
                    text_color = 'text-yellow'
                else:
                    text_color = 'text-green'
                ui.label(avg_saving_ratio_value).classes(f'{text_color} text-xl md:text-3xl font-bold')
            with ui.card().classes('w-full md:w-[23%] flex flex-col items-center justify-center min-w-[200px] bg-secondary h-[15vh]'):
                ui.label('FI Progress').classes('text-xl md:text-3xl font-normal')
                text_color = ''
                if fi_progress < 0.3:
                    text_color = 'text-red'
                elif fi_progress < 0.6:
                    text_color = 'text-orange'
                elif fi_progress < 0.9:
                    text_color = 'text-yellow'
                else:
                    text_color = 'text-green'
                ui.label(fi_progress_value).classes(f'{text_color} text-xl md:text-3xl font-bold')
        # --- Row 2: 2 charts ---
        with ui.row().classes('w-full flex justify-between gap-4 px-4 mt-1 text-primary'):
            with ui.card().classes('w-full md:w-[48%] flex flex-col relative overflow-hidden items-center justify-center bg-secondary'):
                ui.label('Net Worth').classes('text-xl md:text-3xl font-normal')
                net_worth_options = charts.create_net_worth_chart_options(net_worth_data, user_agent)
                ui.echart(options=net_worth_options, theme=theme).classes('w-full h-[30vh]')

            with ui.card().classes('w-full md:w-[48%] flex flex-col relative overflow-hidden items-center justify-center bg-secondary'):
                ui.label('Asset vs Liabilities').classes('text-xl md:text-3xl font-normal')
                asset_vs_liabilities_options = charts.create_asset_vs_liabilities_chart(asset_vs_liabilities_data, user_agent)
                ui.echart(options=asset_vs_liabilities_options, theme=theme).classes('w-full h-[30vh]')

        # --- Row 3: 3 charts ---
        with ui.row().classes('w-full flex justify-between gap-4 px-4 mt-1 text-primary'):
            with ui.card().classes('w-full md:w-[32%] flex flex-col relative overflow-hidden items-center justify-center bg-secondary'):
                    ui.label('Cash Flow').classes('text-xl md:text-3xl font-normal')
                    cash_flow_options = charts.create_cash_flow_options(cash_flow_data, user_agent)
                    ui.echart(options=cash_flow_options, theme=theme).classes('w-full h-[23vh]')
            with ui.card().classes('w-full md:w-[32%] flex flex-col relative overflow-hidden items-center justify-center bg-secondary'):
                    ui.label('Avg Expenses').classes('text-xl md:text-3xl font-normal')
                    expenses_options = charts.create_avg_expenses_options(avg_expenses, user_agent)
                    ui.echart(options=expenses_options, theme=theme).classes('w-full h-[23vh]')
            with ui.card().classes('w-full md:w-[32%] flex flex-col relative overflow-hidden items-center justify-center bg-secondary'):
                    ui.label('Income vs Expenses').classes('text-xl md:text-3xl font-normal')
                    income_vs_expenses_options = charts.create_income_vs_expenses_options(income_vs_expenses_data, user_agent)
                    ui.echart(options=income_vs_expenses_options, theme=theme).classes('w-full h-[23vh]')