from typing import Any, Literal

from nicegui import app, ui

from app.core.constants import (
    CACHE_TTL_SECONDS,
    SAVING_RATIO_THRESHOLD_LOW,
    SAVING_RATIO_THRESHOLD_MEDIUM,
)
from app.core.state_manager import state_manager
from app.services import utils
from app.services.finance_service import FinanceService
from app.ui import charts, dock, header, styles


class HomeRenderer:
    """Home dashboard renderer with clean separation of concerns."""

    def __init__(self):
        """Initialize HomeRenderer with FinanceService."""
        self.finance_service = FinanceService()

    async def load_dashboard_data(self) -> dict[str, Any] | None:
        """Load and cache all dashboard data (KPIs + charts) efficiently.

        This method is more efficient than loading KPIs and charts separately,
        as it creates the FinanceCalculator only once.

        Returns:
            Dictionary with 'kpi_data' and 'chart_data' keys, or None if data unavailable
        """
        if not self.finance_service.has_required_data():
            return None

        def compute_dashboard_data():
            return self.finance_service.get_dashboard_data()

        return await state_manager.get_or_compute(
            user_storage_key="assets_sheet",
            computation_key="dashboard_data",
            compute_fn=compute_dashboard_data,
            ttl_seconds=CACHE_TTL_SECONDS,
        )

    async def load_kpi_data(self) -> dict[str, Any] | None:
        """Load KPI data from dashboard data cache."""
        dashboard_data = await self.load_dashboard_data()
        return dashboard_data["kpi_data"] if dashboard_data else None

    async def load_chart_data(self) -> dict[str, Any] | None:
        """Load chart data from dashboard data cache."""
        dashboard_data = await self.load_dashboard_data()
        return dashboard_data["chart_data"] if dashboard_data else None

    async def render_kpi_cards(self, container: ui.row) -> None:
        """Render KPI cards with real data, replacing skeleton loaders."""
        kpi_data = await self.load_kpi_data()
        container.clear()

        if not kpi_data:
            with container:
                ui.label("No data available").classes("text-center text-gray-500")
            return

        # Get user currency preference
        user_currency: str = app.storage.user.get("currency", utils.get_user_currency())

        with container:
            net_worth_value = utils.format_currency(kpi_data["net_worth"], user_currency)
            mom_variation_percentage_value = utils.format_percentage(
                kpi_data["mom_variation_percentage"], user_currency
            )
            mom_variation_absolute_value = utils.format_currency(
                kpi_data["mom_variation_absolute"], user_currency
            )
            yoy_variation_percentage_value = utils.format_percentage(
                kpi_data["yoy_variation_percentage"], user_currency
            )
            yoy_variation_absolute_value = utils.format_currency(
                kpi_data["yoy_variation_absolute"], user_currency
            )
            avg_saving_ratio_percentage_value = utils.format_percentage(
                kpi_data["avg_saving_ratio_percentage"], user_currency
            )
            avg_saving_ratio_absolute_value = utils.format_currency(
                kpi_data["avg_saving_ratio_absolute"], user_currency
            )

            with (
                ui.card().classes(styles.STAT_CARDS_CLASSES)
                # .classes("cursor-pointer" + styles.STAT_CARDS_CLASSES)
                # .on("click", lambda: ui.navigate.to(pages.NET_WORTH_PAGE))
            ):
                ui.label("Net Worth").classes(styles.STAT_CARDS_LABEL_CLASSES)
                ui.label(net_worth_value).classes(styles.STAT_CARDS_VALUE_CLASSES)
                ui.label("As of " + kpi_data["last_update_date"]).classes(
                    styles.STAT_CARDS_DESC_CLASSES
                )
            with ui.card().classes(styles.STAT_CARDS_CLASSES):
                ui.tooltip("Change vs previous month").classes("tooltip")
                ui.label("MoM Δ").classes(styles.STAT_CARDS_LABEL_CLASSES)
                sign = "+"
                text_color = "text-success"
                if kpi_data["mom_variation_percentage"] < 0:
                    text_color = "text-error"
                    sign = "-"
                ui.label(sign + mom_variation_percentage_value).classes(
                    text_color + styles.STAT_CARDS_VALUE_CLASSES
                )
                ui.label(sign + mom_variation_absolute_value + " compared to last month").classes(
                    styles.STAT_CARDS_DESC_CLASSES
                )
            with ui.card().classes(styles.STAT_CARDS_CLASSES):
                ui.tooltip("Change vs same month last year").classes("tooltip")
                ui.label("YoY Δ").classes(styles.STAT_CARDS_LABEL_CLASSES)
                sign = "+"
                text_color = "text-success"
                if kpi_data["yoy_variation_percentage"] < 0:
                    text_color = "text-error"
                    sign = "-"
                ui.label(sign + yoy_variation_percentage_value).classes(
                    text_color + styles.STAT_CARDS_VALUE_CLASSES
                )
                ui.label(sign + yoy_variation_absolute_value + " compared to last year").classes(
                    styles.STAT_CARDS_DESC_CLASSES
                )
            with ui.card().classes(styles.STAT_CARDS_CLASSES):
                ui.tooltip("Average monthly Saving Ratio of last 12 months").classes("tooltip")
                ui.label("Avg Saving Ratio").classes(styles.STAT_CARDS_LABEL_CLASSES)
                text_color = ""
                if kpi_data["avg_saving_ratio_percentage"] < SAVING_RATIO_THRESHOLD_LOW:
                    text_color = "text-error"
                elif kpi_data["avg_saving_ratio_percentage"] < SAVING_RATIO_THRESHOLD_MEDIUM:
                    text_color = "text-warning"
                else:
                    text_color = "text-success"
                ui.label(avg_saving_ratio_percentage_value).classes(
                    text_color + styles.STAT_CARDS_VALUE_CLASSES
                )
                ui.label(avg_saving_ratio_absolute_value + " saved on average each month").classes(
                    styles.STAT_CARDS_DESC_CLASSES
                )

    async def render_chart(
        self,
        container: ui.card,
        chart_type: Literal[
            "net_worth", "asset_vs_liabilities", "cash_flow", "avg_expenses", "income_vs_expenses"
        ],
        title: str,
    ) -> None:
        """Render a specific chart type into the given container."""
        chart_data = await self.load_chart_data()
        container.clear()

        if not chart_data:
            with container:
                ui.label(title).classes(styles.CHART_CARDS_LABEL_CLASSES)
                ui.label("No data available").classes("text-center text-gray-500")
            return

        user_agent_raw = app.storage.client.get("user_agent")
        if user_agent_raw == "mobile":
            user_agent: Literal["mobile", "desktop"] = "mobile"
        else:
            user_agent = "desktop"
        echart_theme = app.storage.user.get("echarts_theme_url") or ""

        # Get user currency preference
        user_currency: str = app.storage.user.get("currency", utils.get_user_currency())

        with container:
            ui.label(title).classes(styles.CHART_CARDS_LABEL_CLASSES)

            if chart_type == "net_worth":
                options = charts.create_net_worth_chart_options(
                    chart_data["net_worth_data"], user_agent, user_currency
                )
            elif chart_type == "asset_vs_liabilities":
                options = charts.create_asset_vs_liabilities_chart(
                    chart_data["asset_vs_liabilities_data"], user_agent, user_currency
                )
            elif chart_type == "cash_flow":
                options = charts.create_cash_flow_options(
                    chart_data["cash_flow_data"], user_agent, user_currency
                )
            elif chart_type == "avg_expenses":
                options = charts.create_avg_expenses_options(
                    chart_data["avg_expenses"], user_agent, user_currency
                )
            elif chart_type == "income_vs_expenses":
                options = charts.create_income_vs_expenses_options(
                    chart_data["incomes_vs_expenses_data"], user_agent, user_currency
                )

            ui.echart(options=options, theme=echart_theme).classes(
                styles.CHART_CARDS_CHARTS_CLASSES
            )

    def render_skeleton_ui(self) -> dict[str, Any]:
        """Render skeleton UI structure with loading placeholders."""
        with ui.column().classes("w-full max-w-screen-xl mx-auto p-4 space-y-5 main-content"):
            # --- Row 1: KPI cards container ---
            kpi_container = ui.row().classes("grid grid-cols-1 md:grid-cols-4 gap-4 w-full")

            # --- Row 2: 2 charts containers ---
            with ui.row().classes("grid grid-cols-1 lg:grid-cols-2 gap-4 w-full"):
                chart1_container = ui.card().classes(styles.CHART_CARDS_CLASSES)
                chart2_container = ui.card().classes(styles.CHART_CARDS_CLASSES)

            # --- Row 3: 3 charts containers ---
            with ui.row().classes("grid grid-cols-1 lg:grid-cols-3 gap-4 w-full"):
                chart3_container = ui.card().classes(styles.CHART_CARDS_CLASSES)
                chart4_container = ui.card().classes(styles.CHART_CARDS_CLASSES)
                chart5_container = ui.card().classes(styles.CHART_CARDS_CLASSES)

        # Initialize containers with skeleton loaders immediately
        with kpi_container:
            for _ in range(4):
                with ui.card().classes(styles.STAT_CARDS_CLASSES):
                    # Simulate the structure of real KPI cards: label + value + description
                    ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
                        "w-24 h-4 rounded mb-2"  # Title skeleton
                    )
                    ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
                        "w-32 h-8 rounded mb-2"  # Value skeleton (larger)
                    )
                    ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
                        "w-full h-3 rounded"  # Description skeleton
                    )

        for container in [
            chart1_container,
            chart2_container,
            chart3_container,
            chart4_container,
            chart5_container,
        ]:
            with container:
                ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
                    "w-full h-80 rounded-lg"
                )

        return {
            "kpi_container": kpi_container,
            "chart1_container": chart1_container,
            "chart2_container": chart2_container,
            "chart3_container": chart3_container,
            "chart4_container": chart4_container,
            "chart5_container": chart5_container,
        }


def render() -> None:
    """Render the home dashboard with KPI cards and financial charts."""
    header.render()

    # Always render skeleton UI immediately for better UX
    renderer = HomeRenderer()
    containers = renderer.render_skeleton_ui()

    # Check if data needs to be loaded
    assets_sheet = app.storage.user.get("assets_sheet")
    liabilities_sheet = app.storage.user.get("liabilities_sheet")
    expenses_sheet = app.storage.user.get("expenses_sheet")
    incomes_sheet = app.storage.user.get("incomes_sheet")

    if not assets_sheet or not liabilities_sheet or not expenses_sheet or not incomes_sheet:
        # Data not loaded yet - start background loading
        async def load_data_in_background():
            """Load data from Google Sheets in background."""
            from app.services.data_loader import ensure_data_loaded

            try:
                success = await ensure_data_loaded()
                if success:
                    # Data loaded successfully - render components now
                    await renderer.render_kpi_cards(containers["kpi_container"])
                    await renderer.render_chart(
                        containers["chart1_container"], "net_worth", "Net Worth"
                    )
                    await renderer.render_chart(
                        containers["chart2_container"],
                        "asset_vs_liabilities",
                        "Asset vs Liabilities",
                    )
                    await renderer.render_chart(
                        containers["chart3_container"], "cash_flow", "Cash Flow"
                    )
                    await renderer.render_chart(
                        containers["chart4_container"], "avg_expenses", "Avg Expenses"
                    )
                    await renderer.render_chart(
                        containers["chart5_container"], "income_vs_expenses", "Income vs Expenses"
                    )
                else:
                    # Failed to load data - show error
                    containers["kpi_container"].clear()
                    with containers["kpi_container"]:
                        ui.label(
                            "Failed to load data. Please check your configuration in Advanced Settings."
                        ).classes("text-center text-error text-lg col-span-full")
            except Exception as e:
                containers["kpi_container"].clear()
                with containers["kpi_container"]:
                    ui.label(f"Error loading data: {str(e)}").classes(
                        "text-center text-error text-lg col-span-full"
                    )

        # Start loading data asynchronously (non-blocking)
        ui.timer(0.1, load_data_in_background, once=True)
    else:
        # Data already loaded - render components immediately with timers
        ui.timer(0.5, lambda: renderer.render_kpi_cards(containers["kpi_container"]), once=True)
        ui.timer(
            0.5,
            lambda: renderer.render_chart(containers["chart1_container"], "net_worth", "Net Worth"),
            once=True,
        )
        ui.timer(
            0.5,
            lambda: renderer.render_chart(
                containers["chart2_container"], "asset_vs_liabilities", "Asset vs Liabilities"
            ),
            once=True,
        )
        ui.timer(
            0.5,
            lambda: renderer.render_chart(containers["chart3_container"], "cash_flow", "Cash Flow"),
            once=True,
        )
        ui.timer(
            0.5,
            lambda: renderer.render_chart(
                containers["chart4_container"], "avg_expenses", "Avg Expenses"
            ),
            once=True,
        )
        ui.timer(
            0.5,
            lambda: renderer.render_chart(
                containers["chart5_container"], "income_vs_expenses", "Income vs Expenses"
            ),
            once=True,
        )

    dock.render()
