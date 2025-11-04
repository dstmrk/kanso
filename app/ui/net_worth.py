from nicegui import ui

from app.core.constants import CACHE_TTL_SHORT_SECONDS
from app.core.state_manager import state_manager
from app.services.finance_service import FinanceService
from app.ui import charts, header
from app.ui.common import get_user_preferences
from app.ui.components.skeleton import render_large_chart_skeleton
from app.ui.data_loading import render_with_data_loading
from app.ui.rendering_utils import render_no_data_message


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
        ttl_seconds=CACHE_TTL_SHORT_SECONDS,  # 5 minute cache
    )


def render() -> None:
    """Render the Net Worth details page with evolution chart."""
    header.render()

    with ui.column().classes("w-full px-4 mt-4 space-y-4 main-content"):
        # Main chart container - 60vh height for better visualization
        chart_container = (
            ui.card()
            .classes("w-full max-w-screen-xl mx-auto bg-base-100 shadow-md")
            .style("height: 60vh; min-height: 400px;")
        )

        render_large_chart_skeleton(chart_container)

        # Mobile-only message for data tables (hidden on desktop/tablet)
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

        # Desktop/tablet placeholder - future tables (hidden on mobile)
        with (
            ui.card()
            .classes(
                "hidden md:flex w-full max-w-screen-xl mx-auto p-8 items-center justify-center bg-base-100 shadow-md"
            )
            .style("min-height: 200px;")
        ):
            with ui.column().classes("items-center gap-2"):
                ui.icon("table_chart", size="64px").classes("text-base-content/40")
                ui.label("Net Worth Data Table").classes(
                    "text-xl font-semibold text-base-content/70"
                )
                ui.label("Coming in future versions").classes("text-sm text-base-content/60")

    # Render chart with automatic data loading
    async def render_net_worth_chart():
        """Render the net worth evolution chart with loaded data."""
        chart_data = await load_net_worth_evolution_data()

        # Clear skeleton and render chart
        chart_container.clear()

        if not chart_data or not chart_data.get("dates"):
            render_no_data_message(
                chart_container,
                "Net Worth Evolution",
                "Evolution by Asset / Asset Class",
            )
            return

        # Get user preferences using centralized utility
        prefs = get_user_preferences()

        # Create chart options
        options = charts.create_net_worth_evolution_by_class_options(
            chart_data, prefs.user_agent, prefs.currency
        )

        with chart_container:
            ui.label("Net Worth Evolution").classes("text-2xl font-bold p-4")
            ui.tooltip("Evolution by Asset / Asset Class")
            ui.echart(options=options, theme=prefs.echart_theme).classes("w-full h-full p-4")

    render_with_data_loading(
        storage_keys=["assets_sheet", "liabilities_sheet"],
        render_functions=[render_net_worth_chart],
        error_container=chart_container,
    )
