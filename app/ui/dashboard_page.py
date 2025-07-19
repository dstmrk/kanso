
from typing import Dict, Any
from nicegui import ui, app
from app.ui import charts

def create_page(net_worth_data: Dict[str, Any], asset_vs_liabilities_data: Dict[str, Any], net_worth: float, mom_variation: float, avg_saving_ratio: float, fi_progress: float, theme: str, user_agent: str):
    ui.add_head_html('<style>body {background-color: #293441; }</style>')
    ui.colors(primary='#E0E0E0', secondary='#293441', accent='#88B04B')
    
    with ui.column().classes('items-center w-full h-screen max-w-screen-xl mx-auto'):
        ui.label('Personal Finance Dashboard').classes('text-center text-4xl font-bold my-4 text-primary')

        # --- Row 1: KPI cards ---
        with ui.row().classes('w-full flex justify-between gap-4 px-4 text-primary'):
            net_worth_value = '€ {:.2f}'.format(net_worth)
            mom_variation_value = '{:.2%}'.format(mom_variation)
            avg_saving_ratio_value = '{:.2%}'.format(avg_saving_ratio)
            fi_progress_value = '{:.2%}'.format(fi_progress)
            with ui.card().classes('w-full md:w-[23%] flex flex-col items-center justify-center min-w-[200px] bg-secondary'):
                ui.markdown(f'### Net Worth')
                text_color = ''
                if net_worth < 0:
                    text_color = 'text-red'
                ui.markdown(f'## '+ net_worth_value).classes(text_color)
            with ui.card().classes('w-full md:w-[23%] flex flex-col items-center justify-center min-w-[200px] bg-secondary'):
                ui.markdown(f'### MoM Δ')
                text_color = 'text-green'
                if mom_variation < 0:
                    text_color = 'text-red'
                ui.markdown(f'## '+ mom_variation_value).classes(text_color)
            with ui.card().classes('w-full md:w-[23%] flex flex-col items-center justify-center min-w-[200px] bg-secondary'):
                ui.markdown(f'### Avg Saving Ratio')
                text_color = ''
                if avg_saving_ratio < 0.1:
                    text_color = 'text-red'
                elif avg_saving_ratio < 0.3:
                    text_color = 'text-orange'
                elif avg_saving_ratio < 0.5:
                    text_color = 'text-yellow'
                else:
                    text_color = 'text-green'
                ui.markdown(f'## '+ avg_saving_ratio_value).classes(text_color)
            with ui.card().classes('w-full md:w-[23%] flex flex-col items-center justify-center min-w-[200px] bg-secondary'):
                ui.markdown(f'### FI Progress')
                text_color = ''
                if fi_progress < 0.3:
                    text_color = 'text-red'
                elif fi_progress < 0.6:
                    text_color = 'text-orange'
                elif fi_progress < 0.9:
                    text_color = 'text-yellow'
                else:
                    text_color = 'text-green'
                ui.markdown(f'## '+ fi_progress_value).classes(text_color)

        # --- Row 2: 2 charts ---
        with ui.row().classes('w-full flex justify-between gap-4 px-4 mt-4 text-primary'):
            with ui.card().classes('w-full md:w-[48%] flex flex-col relative overflow-hidden items-center justify-center bg-secondary'):
                ui.markdown('### Net Worth').classes('text-center')
                net_worth_options = charts.create_net_worth_chart_options(net_worth_data, user_agent)
                ui.echart(options=net_worth_options, theme=theme).classes('flex-grow')

            with ui.card().classes('w-full md:w-[48%] flex flex-col relative overflow-hidden items-center justify-center bg-secondary'):
                ui.markdown('### Asset vs Liabilities').classes('text-center')
                asset_vs_liabilities_options = charts.create_asset_vs_liabilities_chart(asset_vs_liabilities_data, user_agent)
                ui.echart(options=asset_vs_liabilities_options, theme=theme).classes('flex-grow')

        # --- Row 3: 3 charts ---
        with ui.row().classes('w-full flex justify-between gap-4 px-4 mt-4 text-primary'):
            for title in ['Cash Flow Sankey', 'Avg Expense by Category', 'Income vs Expenses']:
                # Apply the same fix to all chart cards.
                with ui.card().classes('w-full md:w-[32%] flex flex-col relative overflow-hidden items-center justify-center bg-secondary'):
                    ui.markdown(f'### {title}').classes('text-center')
                    ui.echart(options={}, theme=theme).classes('flex-grow')
