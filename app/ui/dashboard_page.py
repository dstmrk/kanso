# app/ui/dashboard_page.py
from nicegui import ui
from app.ui import charts

def create_page(net_worth_data, theme):
    """Builds the entire dashboard UI."""
    # ---- Title ----
    ui.h1('My Personal Finance Dashboard').classes('text-center text-3xl font-bold my-6')

    # ---- First Row: 4 KPI cards ----
    with ui.row().classes('flex flex-wrap gap-4 px-4 justify-center'):
        for title, placeholder in [
            ('Net Worth', '€ XXX 000'),
            ('MoM Δ', '+X %'),
            ('Avg Saving Ratio', 'XX %'),
            ('FI Progress', 'XX %'),
        ]:
            with ui.card().classes('flex-1 min-w-[200px] max-w-[280px] p-4'):
                ui.markdown(f'### {title}')
                ui.markdown(f'## {placeholder}')

    # ---- Second Row: 2 Charts ----
    with ui.row().classes('flex flex-wrap gap-4 px-4 justify-center mt-6'):
        # Net Worth Over Time
        with ui.card().classes('w-full md:w-1/2 p-4'):
            ui.markdown('### Net Worth')
            net_worth_options = charts.create_net_worth_chart_options(net_worth_data)
            ui.echart(options=net_worth_options, theme=theme)
        # Asset vs Liability Sunburst
        with ui.card().classes('w-full md:w-1/2 p-4'):
            ui.markdown('### Asset & Liability Breakdown')
            ui.echart(options={  # ← replace {} with your sunburst options
                # "series": [{"type": "sunburst", "data": [...]}]
            })

    # ---- Third Row: 3 Charts ----
    with ui.row().classes('flex flex-wrap gap-4 px-4 justify-center mt-6'):
        # Sankey Income→Expenses/Savings→Categories
        with ui.card().classes('w-full md:w-1/3 p-4'):
            ui.markdown('### Cash Flow Sankey')
            ui.echart(options={  # ← replace {} with your sankey options
                # "series": [{"type": "sankey", "nodes": [...], "links": [...]}]
            })
        # Average Expense by Category
        with ui.card().classes('w-full md:w-1/3 p-4'):
            ui.markdown('### Avg Expense by Category')
            ui.echart(options={  # ← replace {} with your bar/donut options
                # "xAxis": {...}, "yAxis": {...}, "series": [...]
            })
        # Stocks Investment Performance
        with ui.card().classes('w-full md:w-1/3 p-4'):
            ui.markdown('### Stock Portfolio Performance')
            ui.echart(options={  # ← replace {} with your table‐like or bar chart
                # e.g. bar chart of %‐gain per stock
            })

    #ui.add_head_html('<style>body {background-color: rgba(41,52,65,1); }</style>')
    #with ui.column().classes('w-full items-center'):
    #    with ui.row():
    #        ui.label("Personal Finance Dashboard").tailwind("text-3xl", "text-gray-200")
    #    net_worth_options = charts.create_net_worth_chart_options(net_worth_data)
    #    ui.echart(options=net_worth_options, theme=theme)
