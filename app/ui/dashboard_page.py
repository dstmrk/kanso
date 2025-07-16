# app/ui/dashboard_page.py
from nicegui import ui
from app.ui import charts

# helper to make a flex-column, full-height card
def card_container(width_classes):
    return ui.card().classes(
        f'{width_classes} flex flex-col h-full'
    ).style('min-height: 250px')  # tweak height as needed

def create_page(net_worth_data, theme):
    """Builds the entire dashboard UI."""
    ui.add_head_html('<style>body {background-color: rgba(41,52,65,1); }</style>')
    ui.label('Personal Finance Dashboard').classes('text-center text-3xl font-bold my-6')
    # ---- First Row: 4 KPI cards ----
    with ui.row().classes('flex flex-wrap justify-center gap-4 px-4'):
        for title, value in [
            ('Net Worth', '€ XXX 000'),
            ('MoM Δ', '+X %'),
            ('Avg Saving Ratio', 'XX %'),
            ('FI Progress', 'XX %'),
        ]:
            with card_container('w-full md:w-1/4 min-w-[200px]'):
                ui.markdown(f'### {title}')
                ui.markdown(f'## {value}').classes('mt-auto')  # pushes down
    
    # ---- Second Row: 2 Charts ----
    with ui.row().classes('flex flex-wrap justify-center gap-4 px-4 mt-6'):
        # Net Worth Over Time
        with card_container('w-full md:w-1/2'):
            ui.markdown('### Net Worth')
            net_worth_options = charts.create_net_worth_chart_options(net_worth_data)
            ui.echart(options=net_worth_options, theme=theme).classes('flex-grow')  # replace {} with your options
        # Asset vs Liability Sunburst
        with card_container('w-full md:w-1/2'):
            ui.markdown('### Asset & Liability Breakdown')
            ui.echart(options={},theme=theme).classes('flex-grow')  # replace {} with your options
    
    # ---- Third Row: 3 Charts ----
    with ui.row().classes('flex flex-wrap justify-center gap-4 px-4 mt-6'):
        # Sankey
        with card_container('w-full md:w-1/3'):
            ui.markdown('### Cash Flow Sankey')
            ui.echart(options={},theme=theme).classes('flex-grow')
        # Avg Expense by Category
        with card_container('w-full md:w-1/3'):
            ui.markdown('### Avg Expense by Category')
            ui.echart(options={},theme=theme).classes('flex-grow')
        # Stocks Performance
        with card_container('w-full md:w-1/3'):
            ui.markdown('### Stock Portfolio Performance')
            ui.echart(options={},theme=theme).classes('flex-grow')

