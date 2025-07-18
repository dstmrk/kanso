# app/ui/dashboard_page.py (Corrected Version)

from nicegui import ui, app
from app.ui import charts

def create_page(net_worth_data, asset_vs_liabilities_data, theme, user_agent):
    
    ui.add_head_html('<style>body {background-color: #293441; }</style>')
    ui.colors(primary='#E0E0E0', secondary='#293441', accent='#88B04B')

    with ui.column().classes('items-center w-full h-screen max-w-screen-xl mx-auto'):
        ui.label('Personal Finance Dashboard').classes('text-center text-4xl font-bold my-4 text-primary')

        # --- Row 1: KPI cards ---
        with ui.row().classes('w-full flex justify-between gap-4 px-4 text-primary'):
            for title, value in [
                ('Net Worth', '€ XXX 000'), ('MoM Δ', '+X %'),
                ('Avg Saving Ratio', 'XX %'), ('FI Progress', 'XX %'),
            ]:
                 with ui.card().classes('w-full md:w-[23%] flex flex-col items-center justify-center min-w-[200px] bg-secondary'):
                    ui.markdown(f'### {title}')
                    ui.markdown(f'## {value}').classes('mt-auto')

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
            for title in ['Cash Flow Sankey', 'Avg Expense by Category', 'Expenses by Month']:
                # Apply the same fix to all chart cards.
                with ui.card().classes('w-full md:w-[32%] flex flex-col relative overflow-hidden items-center justify-center bg-secondary'):
                    ui.markdown(f'### {title}').classes('text-center')
                    ui.echart(options={}, theme=theme).classes('flex-grow')
