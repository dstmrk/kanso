"""Expenses page UI with transaction table and visualizations."""

from collections.abc import Callable
from datetime import datetime
from io import StringIO
from typing import Any

import pandas as pd
from nicegui import app, ui

from app.core.constants import (
    CACHE_TTL_SECONDS,
    COL_AMOUNT_PARSED,
    COL_CATEGORY,
    COL_DATE,
    COL_MERCHANT,
    COL_TYPE,
)
from app.core.state_manager import state_manager
from app.logic.finance_calculator import FinanceCalculator
from app.services import utils
from app.ui import charts, header, styles
from app.ui.common import get_user_preferences
from app.ui.components.skeleton import render_chart_skeleton, render_table_skeleton
from app.ui.data_loading import render_with_data_loading
from app.ui.rendering_utils import render_no_data_message


class ExpensesRenderer:
    """Expenses page renderer with table and charts."""

    async def load_expenses_data(self) -> dict[str, Any] | None:
        """Load and cache expenses data from financial records."""
        expenses_sheet_str = app.storage.general.get("expenses_sheet")
        if not expenses_sheet_str:
            return None

        def compute_expenses_data():
            expenses_sheet = utils.read_json(expenses_sheet_str)
            calculator = FinanceCalculator(expenses_df=expenses_sheet)

            # Get processed expenses DataFrame
            processed_df = calculator.processed_expenses_df
            if processed_df is None:
                return None

            # Convert to list of dicts for easier rendering
            # Convert all datetime/Timestamp columns to strings for JSON serialization
            df_copy = processed_df.copy()
            for col in df_copy.columns:
                if df_copy[col].dtype == "datetime64[ns]":
                    df_copy[col] = df_copy[col].astype(str)
            transactions = df_copy.to_dict("records")

            # Get category totals
            category_totals = calculator.get_average_expenses_by_category_last_12_months()

            return {
                "transactions": transactions,
                "category_totals": category_totals,
                "total_count": len(transactions),
            }

        return await state_manager.get_or_compute(
            user_storage_key="expenses_sheet",
            computation_key="expenses_data_v3",  # Changed to force cache refresh with full date format
            compute_fn=compute_expenses_data,
            ttl_seconds=CACHE_TTL_SECONDS,
        )

    async def render_expenses_table(self, container: ui.column) -> None:
        """Render expenses transaction table with all data."""
        expenses_data = await self.load_expenses_data()
        container.clear()

        if not expenses_data or not expenses_data.get("transactions"):
            with container:
                ui.label("No expenses data available").classes("text-center text-gray-500 py-8")
            return

        # Get user currency preference (from general storage - shared across devices)
        user_currency: str = app.storage.general.get("currency", utils.get_user_currency())

        # Mobile-only message (hidden on desktop/tablet)
        with container:
            with (
                ui.card()
                .classes(
                    "w-full max-w-screen-xl mx-auto p-6 flex items-center justify-center bg-base-100 shadow-md md:hidden"
                )
                .style("min-height: 200px;")
            ):
                with ui.column().classes("items-center gap-3 text-center"):
                    ui.icon("table_chart", size="56px").classes("text-base-content/40")
                    ui.label("Where's my data table?").classes(
                        "text-xl font-semibold text-base-content"
                    )
                    ui.label("Data tables are visible on desktop and tablet only").classes(
                        "text-sm text-base-content/60"
                    )

        # Desktop/tablet table (hidden on mobile)
        with container:
            with ui.column().classes("max-md:hidden w-full"):
                with ui.row().classes("w-full justify-between items-center mb-4"):
                    ui.label(f"All Transactions ({expenses_data['total_count']})").classes(
                        "text-xl font-semibold"
                    )

                    with ui.row().classes("gap-2 items-center"):
                        # Global search input
                        search_input = (
                            ui.input(placeholder="Search all fields...")
                            .classes("w-64")
                            .props("outlined dense")
                        )

                        # CSV Export button
                        def export_csv():
                            """Export transactions to CSV file."""
                            # Create DataFrame from transactions
                            df = pd.DataFrame(expenses_data["transactions"])

                            # Select and rename columns for export
                            export_columns = {
                                COL_DATE: "Date",
                                COL_MERCHANT: "Merchant",
                                COL_AMOUNT_PARSED: "Amount",
                                COL_CATEGORY: "Category",
                                COL_TYPE: "Type",
                            }

                            df_export = df[list(export_columns.keys())].copy()
                            df_export.columns = list(export_columns.values())

                            # Generate CSV
                            csv_buffer = StringIO()
                            df_export.to_csv(csv_buffer, index=False)
                            csv_content = csv_buffer.getvalue()

                            # Generate filename with timestamp
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"kanso_expenses_{timestamp}.csv"

                            # Trigger download
                            ui.download(csv_content.encode("utf-8"), filename)
                            ui.notify("✓ CSV exported successfully", type="positive")

                        ui.button(icon="download", on_click=export_csv).props("flat dense").tooltip(
                            "Export to CSV"
                        )

                # Prepare data for AG Grid
                rows = []
                for transaction in expenses_data["transactions"]:
                    # Format amount with currency for display (with 2 decimals)
                    amount_value = transaction.get(COL_AMOUNT_PARSED, 0)
                    formatted_amount = utils.format_currency(
                        amount_value, user_currency, decimals=2
                    )

                    # Keep full date for filtering, will format for display in column config
                    date_str = transaction.get(COL_DATE, "")

                    rows.append(
                        {
                            COL_DATE: date_str,  # Keep full date (YYYY-MM-DD) for proper filtering
                            COL_MERCHANT: transaction.get(COL_MERCHANT, ""),
                            COL_AMOUNT_PARSED: amount_value,
                            "amount_display": formatted_amount,
                            COL_CATEGORY: transaction.get(COL_CATEGORY, ""),
                            COL_TYPE: transaction.get(COL_TYPE, ""),
                        }
                    )

                # AG Grid configuration
                aggrid = ui.aggrid(
                    options={
                        "columnDefs": [
                            {
                                "field": COL_DATE,
                                "headerName": "Date",
                                "sortable": True,
                                "filter": "agDateColumnFilter",
                                "sort": "desc",  # Default sort descending
                                "flex": 1,
                                "minWidth": 120,
                                "valueFormatter": "value ? value.substring(0, 7) : ''",  # Display as YYYY-MM
                            },
                            {
                                "field": COL_MERCHANT,
                                "headerName": "Merchant",
                                "sortable": True,
                                "filter": "agTextColumnFilter",
                                "flex": 2,
                                "minWidth": 150,
                            },
                            {
                                "field": COL_AMOUNT_PARSED,
                                "headerName": "Amount",
                                "sortable": True,
                                "filter": "agNumberColumnFilter",
                                "type": "rightAligned",
                                "cellStyle": {"fontFamily": "monospace"},
                                "flex": 1,
                                "minWidth": 120,
                                "valueFormatter": "value ? value.toLocaleString('de-DE', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' €' : ''",
                            },
                            {
                                "field": COL_CATEGORY,
                                "headerName": "Category",
                                "sortable": True,
                                "filter": "agTextColumnFilter",
                                "flex": 1,
                                "minWidth": 120,
                            },
                            {
                                "field": COL_TYPE,
                                "headerName": "Type",
                                "sortable": True,
                                "filter": "agSetColumnFilter",
                                "flex": 1,
                                "minWidth": 100,
                            },
                        ],
                        "rowData": rows,
                        "defaultColDef": {
                            "resizable": True,
                            "sortable": True,
                            "filter": True,
                        },
                        "pagination": True,
                        "paginationPageSize": 25,
                        "paginationPageSizeSelector": [10, 25],
                        "domLayout": "autoHeight",
                    },
                    theme="quartz",
                    auto_size_columns=False,
                ).classes("w-full")

                # Connect search input to AG Grid quick filter
                search_input.on(
                    "update:model-value",
                    lambda e: aggrid.run_grid_method(
                        "setGridOption", "quickFilterText", e.args or ""
                    ),
                )

    async def _render_chart_generic(
        self,
        container: ui.card,
        title: str,
        tooltip_text: str,
        computation_key: str,
        compute_fn: Callable[[Any], Any],
        chart_options_fn: Callable[..., dict[str, Any]],
        data_validation_key: str | None = None,
    ) -> None:
        """Generic chart rendering with common logic extracted.

        Consolidates the repeated pattern of:
        - Clearing container
        - Loading data from storage
        - Computing/caching results
        - Getting user preferences
        - Rendering chart or error message

        Args:
            container: UI card container to render into
            title: Chart title to display
            tooltip_text: Tooltip text for the chart
            computation_key: Cache key for state_manager
            compute_fn: Function to compute chart data (receives expenses sheet)
            chart_options_fn: Function to create ECharts options
            data_validation_key: Optional key to validate data exists (e.g., "months")
        """
        container.clear()

        # Load expenses sheet from storage
        expenses_sheet_str = app.storage.general.get("expenses_sheet")
        if not expenses_sheet_str:
            render_no_data_message(container, title, tooltip_text)
            return

        # Compute or retrieve cached data
        def compute_wrapper():
            expenses_sheet = utils.read_json(expenses_sheet_str)
            calculator = FinanceCalculator(expenses_df=expenses_sheet)
            return compute_fn(calculator)

        data = await state_manager.get_or_compute(
            user_storage_key="expenses_sheet",
            computation_key=computation_key,
            compute_fn=compute_wrapper,
            ttl_seconds=CACHE_TTL_SECONDS,
        )

        # Validate data
        if not data or (data_validation_key and not data.get(data_validation_key)):
            render_no_data_message(container, title, tooltip_text)
            return

        # Get user preferences using centralized utility
        prefs = get_user_preferences()

        # Create chart options
        options = chart_options_fn(data, prefs.user_agent, prefs.currency)

        # Render chart
        with container:
            ui.label(title).classes(styles.CHART_CARDS_LABEL_CLASSES)
            ui.tooltip(tooltip_text)
            ui.echart(options=options, theme=prefs.echart_theme).classes("h-96 w-full")

    async def render_yoy_chart(self, container: ui.card) -> None:
        """Render year-over-year expenses comparison chart."""
        await self._render_chart_generic(
            container=container,
            title="Year-over-Year Expenses",
            tooltip_text="Cumulative + Forecast until EoY",
            computation_key="expenses_yoy_comparison_v2",
            compute_fn=lambda calc: calc.get_expenses_yoy_comparison(),
            chart_options_fn=charts.create_expenses_yoy_comparison_options,
            data_validation_key="months",
        )

    async def render_merchant_chart(self, container: ui.card) -> None:
        """Render expenses by merchant donut chart."""
        await self._render_chart_generic(
            container=container,
            title="Expenses by Merchant",
            tooltip_text="Expenses of last 12 months",
            computation_key="expenses_by_merchant_v1",
            compute_fn=lambda calc: calc.get_expenses_by_merchant_last_12_months(),
            chart_options_fn=charts.create_expenses_by_merchant_options,
        )

    async def render_type_chart(self, container: ui.card) -> None:
        """Render expenses by type donut chart."""
        await self._render_chart_generic(
            container=container,
            title="Expenses by Type",
            tooltip_text="Expenses of last 12 months",
            computation_key="expenses_by_type_v1",
            compute_fn=lambda calc: calc.get_expenses_by_type_last_12_months(),
            chart_options_fn=charts.create_expenses_by_type_options,
        )

    def render_skeleton_ui(self) -> dict[str, Any]:
        """Render skeleton UI structure with loading placeholders."""
        with ui.column().classes("w-full max-w-screen-xl mx-auto p-4 space-y-5 main-content"):
            # Row with 3 chart containers
            with ui.row().classes("grid grid-cols-1 lg:grid-cols-3 gap-4 w-full"):
                yoy_chart_container = ui.card().classes(styles.CHART_CARDS_CLASSES)
                merchant_chart_container = ui.card().classes(styles.CHART_CARDS_CLASSES)
                type_chart_container = ui.card().classes(styles.CHART_CARDS_CLASSES)

            # Table container
            table_container = ui.column().classes("w-full")

        # Initialize chart containers with skeletons
        render_chart_skeleton(yoy_chart_container)
        render_chart_skeleton(merchant_chart_container)
        render_chart_skeleton(type_chart_container)

        # Initialize table container with skeleton
        render_table_skeleton(table_container)

        return {
            "yoy_chart_container": yoy_chart_container,
            "merchant_chart_container": merchant_chart_container,
            "type_chart_container": type_chart_container,
            "table_container": table_container,
        }


def render() -> None:
    """Render the expenses page with transaction table and charts."""
    header.render()

    # Always render skeleton UI immediately for better UX
    renderer = ExpensesRenderer()
    containers = renderer.render_skeleton_ui()

    # Render components with automatic data loading
    render_with_data_loading(
        storage_keys=["expenses_sheet"],
        render_functions=[
            lambda: renderer.render_yoy_chart(containers["yoy_chart_container"]),
            lambda: renderer.render_merchant_chart(containers["merchant_chart_container"]),
            lambda: renderer.render_type_chart(containers["type_chart_container"]),
            lambda: renderer.render_expenses_table(containers["table_container"]),
        ],
        error_container=containers["table_container"],
    )
