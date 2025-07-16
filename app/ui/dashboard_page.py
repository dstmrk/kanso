# app/ui/dashboard_page.py
from nicegui import ui
from typing import Dict, Any
from app.ui import charts

DUMMY_CHART_OPTIONS = {"xAxis": {"type": "category"}, "yAxis": {"type": "value"}, "series": [{"type": "line"}]}

def create_page(net_worth_data: Dict[str, Any],
                asset_liability_data: Dict[str, Any],
                # Add other data parameters as needed for the new charts
                ) -> None:
    """
    Builds the dashboard UI with a specific responsive grid layout and equal height cards.
    """
    # Main container to center all content on the page
    with ui.column().classes('w-full items-center'):
        ui.label("Personal Finance Dashboard").classes("text-h4 font-bold text-center my-4")
        # --- ROW 1: FOUR EQUAL COLUMNS ---
        # On mobile (default), cards are full-width. On medium screens and up (md:), they are 1/4 width.
        with ui.row().classes('w-full justify-center gap-4'):
            for i in range(4): # Loop to create 4 cards
                with ui.card().classes('w-full md:w-1/4 flex flex-col'):
                    # You can use real data here. This is a placeholder.
                    if i == 0:
                        ui.label('Net Worth Over Time').classes('text-center font-bold')
                        chart_options = charts.create_net_worth_chart_options(net_worth_data)
                    else:
                        ui.label(f'Chart 1.{i+1}').classes('text-center font-bold')
                        chart_options = DUMMY_CHART_OPTIONS # Placeholder
                    
                    # 'flex-grow' ensures the chart expands to fill the card vertically
                    ui.echart(chart_options, theme='my_theme').classes('flex-grow h-80')
        # --- ROW 2: TWO EQUAL COLUMNS ---
        # On mobile, full-width. On desktop (md:), half-width.
        # 'mt-8' adds margin-top for vertical spacing between rows.
        with ui.row().classes('w-full justify-center gap-4 mt-8'):
            # First card in the second row
            with ui.card().classes('w-full md:w-1/2 flex flex-col'):
                ui.label('Asset vs. Liabilities').classes('text-center font-bold')
                asset_liability_options = charts.create_asset_liability_chart_options(asset_liability_data)
                ui.echart(asset_liability_options, theme='my_theme').classes('flex-grow h-80')
            # Second card in the second row
            with ui.card().classes('w-full md:w-1/2 flex flex-col'):
                ui.label('Chart 2.2').classes('text-center font-bold')
                chart_options = DUMMY_CHART_OPTIONS # Placeholder
                ui.echart(chart_options, theme='my_theme').classes('flex-grow h-80')
        # --- ROW 3: THREE EQUAL COLUMNS ---
        # On mobile, full-width. On desktop (md:), one-third width.
        with ui.row().classes('w-full justify-center gap-4 mt-8'):
            for i in range(3): # Loop to create 3 cards
                with ui.card().classes('w-full md:w-1/3 flex flex-col'):
                    ui.label(f'KPI Card 3.{i+1}').classes('text-center font-bold')
                    # The 'flex-grow' on a container will ensure alignment.
                    with ui.column().classes('flex-grow items-center justify-center'):
                        ui.label(f'€{(i+1)*12345:,.2f}').classes('text-h4')
