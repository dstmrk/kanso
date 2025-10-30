"""Expenses page UI with transaction table and visualizations."""

from typing import Any, Literal

from nicegui import app, ui

from app.core.constants import (
    COL_AMOUNT_PARSED,
    COL_CATEGORY,
    COL_DATE,
    COL_MERCHANT,
    COL_TYPE,
)
from app.core.state_manager import state_manager
from app.logic.finance_calculator import FinanceCalculator
from app.services import utils
from app.ui import charts, dock, header, styles


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
            computation_key="expenses_data_v2",  # Changed to force cache refresh
            compute_fn=compute_expenses_data,
            ttl_seconds=86400,
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

        with container:
            ui.label(f"All Transactions ({expenses_data['total_count']})").classes(
                "text-xl font-semibold mb-4"
            )

            # Create table with all transactions
            columns: list[dict[str, Any]] = [
                {"name": "date", "label": "Date", "field": COL_DATE, "align": "left"},
                {"name": "merchant", "label": "Merchant", "field": COL_MERCHANT, "align": "left"},
                {
                    "name": "amount",
                    "label": "Amount",
                    "field": COL_AMOUNT_PARSED,
                    "align": "right",
                    "sortable": True,
                },
                {"name": "category", "label": "Category", "field": COL_CATEGORY, "align": "left"},
                {"name": "type", "label": "Type", "field": COL_TYPE, "align": "left"},
            ]

            rows = []
            for transaction in expenses_data["transactions"]:
                # Format amount with currency
                amount_value = transaction.get(COL_AMOUNT_PARSED, 0)
                formatted_amount = utils.format_currency(amount_value, user_currency)

                rows.append(
                    {
                        COL_DATE: transaction.get(COL_DATE, ""),
                        COL_MERCHANT: transaction.get(COL_MERCHANT, ""),
                        COL_AMOUNT_PARSED: amount_value,
                        "amount_display": formatted_amount,
                        COL_CATEGORY: transaction.get(COL_CATEGORY, ""),
                        COL_TYPE: transaction.get(COL_TYPE, ""),
                    }
                )

            table = ui.table(
                columns=columns,
                rows=rows,
                row_key="Date",
                pagination={"rowsPerPage": 20, "sortBy": "date", "descending": True},
            ).classes("w-full")

            # Custom cell rendering for amount with currency format
            table.add_slot(
                "body-cell-amount",
                r"""
                <q-td :props="props">
                    <div class="text-right font-mono">
                        {{ props.row.amount_display }}
                    </div>
                </q-td>
                """,
            )

    async def render_yoy_chart(self, container: ui.card) -> None:
        """Render year-over-year expenses comparison chart."""
        # Clear skeleton and render chart
        container.clear()

        # Load expenses and calculate YoY data
        expenses_sheet_str = app.storage.general.get("expenses_sheet")
        if not expenses_sheet_str:
            with container:
                ui.label("Year-over-Year Expenses").classes(styles.CHART_CARDS_LABEL_CLASSES)
                ui.tooltip("Cumulative + Forecast until EoY")
                ui.label("No data available").classes("text-center text-gray-500 p-8")
            return

        def compute_yoy_data():
            expenses_sheet = utils.read_json(expenses_sheet_str)
            calculator = FinanceCalculator(expenses_df=expenses_sheet)
            return calculator.get_expenses_yoy_comparison()

        yoy_data = await state_manager.get_or_compute(
            user_storage_key="expenses_sheet",
            computation_key="expenses_yoy_comparison_v2",  # Changed to force cache refresh
            compute_fn=compute_yoy_data,
            ttl_seconds=86400,
        )

        if not yoy_data or not yoy_data.get("months"):
            with container:
                ui.label("Year-over-Year Expenses").classes(styles.CHART_CARDS_LABEL_CLASSES)
                ui.tooltip("Cumulative + Forecast until EoY")
                ui.label("No data available").classes("text-center text-gray-500 p-8")
            return

        user_agent_raw = app.storage.client.get("user_agent")
        user_agent: Literal["mobile", "desktop"]
        if user_agent_raw == "mobile":
            user_agent = "mobile"
        else:
            user_agent = "desktop"
        echart_theme = app.storage.general.get("echarts_theme_url") or ""

        # Get user currency preference (from general storage - shared across devices)
        user_currency: str = app.storage.general.get("currency", utils.get_user_currency())

        # Create chart options for YoY comparison
        options = charts.create_expenses_yoy_comparison_options(yoy_data, user_agent, user_currency)

        with container:
            ui.label("Year-over-Year Expenses").classes(styles.CHART_CARDS_LABEL_CLASSES)
            ui.tooltip("Cumulative + Forecast until EoY")
            ui.echart(options=options, theme=echart_theme).classes(
                styles.CHART_CARDS_CHARTS_CLASSES
            )

    async def render_merchant_chart(self, container: ui.card) -> None:
        """Render expenses by merchant donut chart."""
        # Clear skeleton and render chart
        container.clear()

        # Load expenses and calculate merchant distribution
        expenses_sheet_str = app.storage.general.get("expenses_sheet")
        if not expenses_sheet_str:
            with container:
                ui.label("Expenses by Merchant").classes(styles.CHART_CARDS_LABEL_CLASSES)
                ui.tooltip("Expenses of last 12 months")
                ui.label("No data available").classes("text-center text-gray-500 p-8")
            return

        def compute_merchant_data():
            expenses_sheet = utils.read_json(expenses_sheet_str)
            calculator = FinanceCalculator(expenses_df=expenses_sheet)
            return calculator.get_expenses_by_merchant_last_12_months()

        merchant_data = await state_manager.get_or_compute(
            user_storage_key="expenses_sheet",
            computation_key="expenses_by_merchant_v1",
            compute_fn=compute_merchant_data,
            ttl_seconds=86400,
        )

        if not merchant_data:
            with container:
                ui.label("Expenses by Merchant").classes(styles.CHART_CARDS_LABEL_CLASSES)
                ui.tooltip("Expenses of last 12 months")
                ui.label("No data available").classes("text-center text-gray-500 p-8")
            return

        user_agent_raw = app.storage.client.get("user_agent")
        user_agent: Literal["mobile", "desktop"]
        if user_agent_raw == "mobile":
            user_agent = "mobile"
        else:
            user_agent = "desktop"
        echart_theme = app.storage.general.get("echarts_theme_url") or ""

        # Get user currency preference
        user_currency: str = app.storage.general.get("currency", utils.get_user_currency())

        # Create chart options for merchant distribution
        options = charts.create_expenses_by_merchant_options(
            merchant_data, user_agent, user_currency
        )

        with container:
            ui.label("Expenses by Merchant").classes(styles.CHART_CARDS_LABEL_CLASSES)
            ui.tooltip("Expenses of last 12 months")
            ui.echart(options=options, theme=echart_theme).classes(
                styles.CHART_CARDS_CHARTS_CLASSES
            )

    async def render_type_chart(self, container: ui.card) -> None:
        """Render expenses by type donut chart."""
        # Clear skeleton and render chart
        container.clear()

        # Load expenses and calculate type distribution
        expenses_sheet_str = app.storage.general.get("expenses_sheet")
        if not expenses_sheet_str:
            with container:
                ui.label("Expenses by Type").classes(styles.CHART_CARDS_LABEL_CLASSES)
                ui.tooltip("Expenses of last 12 months")
                ui.label("No data available").classes("text-center text-gray-500 p-8")
            return

        def compute_type_data():
            expenses_sheet = utils.read_json(expenses_sheet_str)
            calculator = FinanceCalculator(expenses_df=expenses_sheet)
            return calculator.get_expenses_by_type_last_12_months()

        type_data = await state_manager.get_or_compute(
            user_storage_key="expenses_sheet",
            computation_key="expenses_by_type_v1",
            compute_fn=compute_type_data,
            ttl_seconds=86400,
        )

        if not type_data:
            with container:
                ui.label("Expenses by Type").classes(styles.CHART_CARDS_LABEL_CLASSES)
                ui.tooltip("Expenses of last 12 months")
                ui.label("No data available").classes("text-center text-gray-500 p-8")
            return

        user_agent_raw = app.storage.client.get("user_agent")
        user_agent: Literal["mobile", "desktop"]
        if user_agent_raw == "mobile":
            user_agent = "mobile"
        else:
            user_agent = "desktop"
        echart_theme = app.storage.general.get("echarts_theme_url") or ""

        # Get user currency preference
        user_currency: str = app.storage.general.get("currency", utils.get_user_currency())

        # Create chart options for type distribution
        options = charts.create_expenses_by_type_options(type_data, user_agent, user_currency)

        with container:
            ui.label("Expenses by Type").classes(styles.CHART_CARDS_LABEL_CLASSES)
            ui.tooltip("Expenses of last 12 months")
            ui.echart(options=options, theme=echart_theme).classes(
                styles.CHART_CARDS_CHARTS_CLASSES
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

        # Initialize chart containers with skeletons (title + chart)
        with yoy_chart_container:
            # Title skeleton
            ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
                "w-48 h-6 rounded mb-4"
            )
            # Chart skeleton
            ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
                "w-full h-64 rounded-lg"
            )

        with merchant_chart_container:
            # Title skeleton
            ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
                "w-48 h-6 rounded mb-4"
            )
            # Chart skeleton
            ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
                "w-full h-64 rounded-lg"
            )

        with type_chart_container:
            # Title skeleton
            ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
                "w-48 h-6 rounded mb-4"
            )
            # Chart skeleton
            ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
                "w-full h-64 rounded-lg"
            )

        # Initialize table container with skeleton
        with table_container:
            ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
                "w-full h-96 rounded-lg"
            )

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

    # Check if expenses data is loaded
    expenses_sheet = app.storage.general.get("expenses_sheet")

    if not expenses_sheet:
        # Data not loaded yet - start background loading
        async def load_data_in_background():
            """Load expenses data from Google Sheets in background."""
            from app.services.data_loader import ensure_data_loaded

            try:
                success = await ensure_data_loaded()
                if success:
                    # Data loaded successfully - render components now
                    await renderer.render_yoy_chart(containers["yoy_chart_container"])
                    await renderer.render_merchant_chart(containers["merchant_chart_container"])
                    await renderer.render_type_chart(containers["type_chart_container"])
                    await renderer.render_expenses_table(containers["table_container"])
                else:
                    # Failed to load data - show error
                    containers["table_container"].clear()
                    with containers["table_container"]:
                        ui.label(
                            "Failed to load data. Please check your configuration in Advanced Settings."
                        ).classes("text-center text-error text-lg")
            except Exception as e:
                containers["table_container"].clear()
                with containers["table_container"]:
                    ui.label(f"Error loading data: {str(e)}").classes(
                        "text-center text-error text-lg"
                    )

        # Start loading data asynchronously (non-blocking)
        ui.timer(0.1, load_data_in_background, once=True)
    else:
        # Data already loaded - render components immediately with timers
        ui.timer(
            0.5,
            lambda: renderer.render_yoy_chart(containers["yoy_chart_container"]),
            once=True,
        )
        ui.timer(
            0.5,
            lambda: renderer.render_merchant_chart(containers["merchant_chart_container"]),
            once=True,
        )
        ui.timer(
            0.5,
            lambda: renderer.render_type_chart(containers["type_chart_container"]),
            once=True,
        )
        ui.timer(
            0.5,
            lambda: renderer.render_expenses_table(containers["table_container"]),
            once=True,
        )

    dock.render()
