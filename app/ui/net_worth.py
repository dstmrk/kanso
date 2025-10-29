from typing import Literal

from nicegui import app, ui

from app.core.state_manager import state_manager
from app.services import utils
from app.services.finance_service import FinanceService
from app.ui import charts, dock, header, styles


async def load_net_worth_evolution_data():
    """Load net worth evolution data with caching."""
    finance_service = FinanceService()

    if not finance_service.has_required_data():
        return None

    def compute_net_worth_evolution():
        calculator = finance_service.get_calculator()
        if calculator:
            return calculator.get_monthly_net_worth_by_asset_class()
        return None

    return await state_manager.get_or_compute(
        user_storage_key="assets_sheet",
        computation_key="net_worth_evolution_by_class_v4",  # Changed to force cache refresh
        compute_fn=compute_net_worth_evolution,
        ttl_seconds=300,  # 5 minute cache
    )


def render() -> None:
    """Render the Net Worth details page with evolution chart."""
    header.render()

    with ui.column().classes("w-full px-4 mt-4 space-y-4 main-content"):
        # Main chart container - 40vh height
        chart_container = (
            ui.card()
            .classes("w-full max-w-screen-xl mx-auto bg-base-100 shadow-md")
            .style("height: 40vh; min-height: 300px;")
        )

        with chart_container:
            # Header with title
            ui.label("Net Worth Evolution by Asset Class").classes("text-2xl font-bold p-4")

            # Skeleton loader
            chart_skeleton = ui.column().classes("w-full h-full p-4")
            with chart_skeleton:
                ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
                    "w-full h-full rounded-lg"
                )

        # Placeholder section - future tables
        with (
            ui.card()
            .classes(
                "w-full max-w-screen-xl mx-auto p-8 flex items-center justify-center bg-base-100 shadow-md"
            )
            .style("min-height: 200px;")
        ):
            with ui.column().classes("items-center gap-2"):
                ui.icon("table_chart", size="64px").classes("text-gray-400")
                ui.label("📊 Net Worth Data Table").classes("text-xl font-semibold text-gray-500")
                ui.label("Coming in future versions").classes("text-sm text-gray-400")

    dock.render()

    # Load data asynchronously
    async def render_chart():
        """Render the chart with loaded data."""
        chart_data = await load_net_worth_evolution_data()

        # Clear skeleton and render chart
        chart_skeleton.clear()

        if not chart_data or not chart_data.get("dates"):
            with chart_skeleton:
                ui.label("No data available").classes("text-center text-gray-500 p-8")
            return

        # Get user preferences
        user_agent_raw = app.storage.client.get("user_agent")
        if user_agent_raw == "mobile":
            user_agent: Literal["mobile", "desktop"] = "mobile"
        else:
            user_agent = "desktop"
        user_currency: str = app.storage.general.get("currency", utils.get_user_currency())
        echart_theme = app.storage.general.get("echarts_theme_url") or ""

        # Create chart options
        options = charts.create_net_worth_evolution_by_class_options(
            chart_data, user_agent, user_currency
        )

        with chart_skeleton:
            ui.echart(options=options, theme=echart_theme).classes("w-full h-full")

    # Trigger async data loading
    ui.timer(0.1, render_chart, once=True)
