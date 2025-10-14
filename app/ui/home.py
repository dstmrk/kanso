from typing import Any, Literal

from nicegui import app, ui

from app.core.state_manager import state_manager
from app.logic.finance_calculator import FinanceCalculator
from app.services import utils
from app.ui import charts, dock, header, styles


class HomeRenderer:
    """Home dashboard renderer with clean separation of concerns."""

    async def load_kpi_data(self) -> dict[str, Any] | None:
        """Load and cache key performance indicators from financial data."""
        data_sheet_str = app.storage.user.get("data_sheet")
        if not data_sheet_str:
            return None

        def compute_kpi_data():
            data_sheet = utils.read_json(data_sheet_str)
            calculator = FinanceCalculator(data_sheet)

            return {
                "last_update_date": calculator.get_last_update_date(),
                "net_worth": calculator.get_current_net_worth(),
                "mom_variation_percentage": calculator.get_month_over_month_net_worth_variation_percentage(),
                "mom_variation_absolute": calculator.get_month_over_month_net_worth_variation_absolute(),
                "yoy_variation_percentage": calculator.get_year_over_year_net_worth_variation_percentage(),
                "yoy_variation_absolute": calculator.get_year_over_year_net_worth_variation_absolute(),
                "avg_saving_ratio_percentage": calculator.get_average_saving_ratio_last_12_months_percentage(),
                "avg_saving_ratio_absolute": calculator.get_average_saving_ratio_last_12_months_absolute(),
            }

        return await state_manager.get_or_compute(
            user_storage_key="data_sheet",
            computation_key="kpi_data",
            compute_fn=compute_kpi_data,
            ttl_seconds=86400,
        )

    async def load_chart_data(self) -> dict[str, Any] | None:
        """Load and cache chart data for dashboard visualizations."""
        data_sheet_str = app.storage.user.get("data_sheet")
        assets_sheet_str = app.storage.user.get("assets_sheet")
        liabilities_sheet_str = app.storage.user.get("liabilities_sheet")
        expenses_sheet_str = app.storage.user.get("expenses_sheet")

        if not data_sheet_str or not expenses_sheet_str:
            return None

        def compute_chart_data():
            data_sheet = utils.read_json(data_sheet_str)
            assets_sheet = utils.read_json(assets_sheet_str)
            liabilities_sheet = utils.read_json(liabilities_sheet_str)
            expenses_sheet = utils.read_json(expenses_sheet_str)
            calculator = FinanceCalculator(
                data_sheet, assets_sheet, liabilities_sheet, expenses_sheet
            )

            return {
                "net_worth_data": calculator.get_monthly_net_worth(),
                "asset_vs_liabilities_data": calculator.get_assets_liabilities(),
                "incomes_vs_expenses_data": calculator.get_incomes_vs_expenses(),
                "cash_flow_data": calculator.get_cash_flow_last_12_months(),
                "avg_expenses": calculator.get_average_expenses_by_category_last_12_months(),
            }

        return await state_manager.get_or_compute(
            user_storage_key="data_sheet",
            computation_key="chart_data",
            compute_fn=compute_chart_data,
            ttl_seconds=86400,
        )

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
                if kpi_data["avg_saving_ratio_percentage"] < 0.2:
                    text_color = "text-error"
                elif kpi_data["avg_saving_ratio_percentage"] < 0.4:
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
                ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
                    styles.STAT_CARDS_CLASSES + " h-20"
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
    data_sheet = app.storage.user.get("data_sheet")
    expenses_sheet = app.storage.user.get("expenses_sheet")

    header.render()

    if not data_sheet or not expenses_sheet:
        with ui.column().classes("w-full max-w-screen-xl mx-auto p-4 space-y-5 main-content"):
            ui.label("No data available. Please upload your data files.").classes(
                "text-center text-gray-500 text-lg"
            )
        dock.render()
        return

    renderer = HomeRenderer()
    containers = renderer.render_skeleton_ui()

    # Start loading components with individual timers for progressive rendering
    ui.timer(0.1, lambda: renderer.render_kpi_cards(containers["kpi_container"]), once=True)
    ui.timer(
        0.1,
        lambda: renderer.render_chart(containers["chart1_container"], "net_worth", "Net Worth"),
        once=True,
    )
    ui.timer(
        0.1,
        lambda: renderer.render_chart(
            containers["chart2_container"], "asset_vs_liabilities", "Asset vs Liabilities"
        ),
        once=True,
    )
    ui.timer(
        0.1,
        lambda: renderer.render_chart(containers["chart3_container"], "cash_flow", "Cash Flow"),
        once=True,
    )
    ui.timer(
        0.1,
        lambda: renderer.render_chart(
            containers["chart4_container"], "avg_expenses", "Avg Expenses"
        ),
        once=True,
    )
    ui.timer(
        0.1,
        lambda: renderer.render_chart(
            containers["chart5_container"], "income_vs_expenses", "Income vs Expenses"
        ),
        once=True,
    )

    dock.render()
