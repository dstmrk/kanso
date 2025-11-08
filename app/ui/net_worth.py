import logging

import pandas as pd
from nicegui import ui

from app.core.constants import (
    AGGRID_PAGE_SIZE_DEFAULT,
    AGGRID_PAGE_SIZE_OPTIONS,
    CACHE_TTL_SHORT_SECONDS,
    COL_DATE_DT,
)
from app.core.state_manager import state_manager
from app.logic.table_formatters import (
    build_aggrid_columns_from_dataframe,
    prepare_dataframe_for_aggrid,
)
from app.services.finance_service import FinanceService
from app.ui import charts, header, styles
from app.ui.common import get_aggrid_currency_formatter, get_user_preferences
from app.ui.components.skeleton import render_large_chart_skeleton, render_table_skeleton
from app.ui.data_loading import render_with_data_loading
from app.ui.rendering_utils import render_no_data_message
from app.ui.table_utils import create_csv_export_button, render_mobile_table_message


async def load_net_worth_evolution_data():
    """Load net worth evolution data with caching.

    Returns:
        Chart data dictionary or None if data unavailable or error occurs
    """
    try:
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
            computation_key="net_worth_evolution_by_class_v4",
            compute_fn=compute_net_worth_evolution,
            ttl_seconds=CACHE_TTL_SHORT_SECONDS,
        )
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error loading net worth evolution data: {e}", exc_info=True)
        return None


async def load_assets_liabilities_data() -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """Load assets and liabilities DataFrames, filtered to valid dates.

    Uses the same date filtering logic as the net worth chart: only shows dates
    up to the most recent date in the Incomes sheet (no future dates).

    Returns:
        Tuple of (assets_df, liabilities_df), either can be None if data unavailable or error occurs
    """
    try:
        finance_service = FinanceService()

        if not finance_service.has_required_data():
            return None, None

        calculator = finance_service.get_calculator()
        if not calculator:
            return None, None

        # Get valid dates from net worth calculation (filtered by max income date)
        nw_data = calculator.get_monthly_net_worth()
        valid_dates = nw_data.get("dates", [])

        if not valid_dates:
            return None, None

        # Get full DataFrames
        assets_df = calculator.processed_assets_df
        liabilities_df = calculator.processed_liabilities_df

        # Filter to valid dates only (same logic as charts)
        filtered_assets = None
        if assets_df is not None and not assets_df.empty:
            filtered_assets = assets_df[
                assets_df[COL_DATE_DT].dt.strftime("%Y-%m").isin(valid_dates)
            ].copy()

        filtered_liabilities = None
        if liabilities_df is not None and not liabilities_df.empty:
            filtered_liabilities = liabilities_df[
                liabilities_df[COL_DATE_DT].dt.strftime("%Y-%m").isin(valid_dates)
            ].copy()

        return filtered_assets, filtered_liabilities
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error loading assets/liabilities data: {e}", exc_info=True)
        return None, None


def render() -> None:
    """Render the Net Worth details page with evolution chart."""
    ui.add_head_html(styles.AGGRID_DAISY_THEME_CSS)
    header.render()

    with ui.column().classes("w-full px-4 mt-4 space-y-4 main-content"):
        # Main chart container - 60vh height for better visualization
        chart_container = (
            ui.card()
            .classes("w-full max-w-screen-xl mx-auto bg-base-100 shadow-md")
            .style("height: 60vh; min-height: 400px;")
        )

        # Wrapper with padding to match tab panels
        with chart_container:
            skeleton_wrapper = ui.column().classes("w-full h-full p-4")

        render_large_chart_skeleton(skeleton_wrapper)

        # Mobile-only message for data tables (hidden on desktop/tablet)
        render_mobile_table_message()

        # Data tables in tabs (hidden on mobile)
        with ui.card().classes(
            "max-md:hidden w-full max-w-screen-xl mx-auto bg-base-100 shadow-md"
        ):
            with ui.tabs().classes("w-full") as tabs:
                assets_tab = ui.tab("Assets")
                liabilities_tab = ui.tab("Liabilities")

            with (
                ui.tab_panels(tabs, value=assets_tab)
                .classes("w-full bg-base-100")
                .style("overflow: visible;")
            ):
                with (
                    ui.tab_panel(assets_tab)
                    .classes("overflow-visible")
                    .style("min-height: auto; height: auto;")
                ):
                    assets_container = ui.column().classes("w-full")
                    render_table_skeleton(assets_container, height="h-64")

                with (
                    ui.tab_panel(liabilities_tab)
                    .classes("overflow-visible")
                    .style("min-height: auto; height: auto;")
                ):
                    liabilities_container = ui.column().classes("w-full")
                    render_table_skeleton(liabilities_container, height="h-64")

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

    async def render_assets_liabilities_tables():
        """Render assets and liabilities tables."""
        assets_df, liabilities_df = await load_assets_liabilities_data()

        # Render Assets table
        assets_container.clear()
        if assets_df is not None and not assets_df.empty:
            with assets_container:
                render_single_table(df=assets_df, table_id="assets_table")
        else:
            with assets_container:
                ui.label("No assets data available").classes("text-lg p-4 text-base-content/60")

        # Render Liabilities table
        liabilities_container.clear()
        if liabilities_df is not None and not liabilities_df.empty:
            with liabilities_container:
                render_single_table(df=liabilities_df, table_id="liabilities_table")
        else:
            with liabilities_container:
                ui.label("No liabilities data available").classes(
                    "text-lg p-4 text-base-content/60"
                )

    def render_single_table(df: pd.DataFrame, table_id: str) -> None:
        """Render a single AG Grid table with CSV export.

        Args:
            df: DataFrame to display.
            table_id: Unique ID for this table instance (e.g., "assets_table").
        """
        logger = logging.getLogger(__name__)

        try:
            # Get user currency preferences
            prefs = get_user_preferences()
            currency_formatter = get_aggrid_currency_formatter(prefs.currency)

            # Export button only
            with ui.row().classes("w-full justify-end items-center mb-4 px-4 pt-4"):
                create_csv_export_button(
                    df=df, filename_prefix=f"kanso_{table_id}", columns_to_drop=[COL_DATE_DT]
                )

            # Build AG Grid columns and rows
            column_defs = build_aggrid_columns_from_dataframe(df, currency_formatter)
            rows = prepare_dataframe_for_aggrid(df)

            # Render AG Grid table
            ui.aggrid(
                options={
                    "columnDefs": column_defs,
                    "rowData": rows,
                    "defaultColDef": {
                        "resizable": True,
                        "sortable": True,
                    },
                    "pagination": True,
                    "paginationPageSize": AGGRID_PAGE_SIZE_DEFAULT,
                    "paginationPageSizeSelector": AGGRID_PAGE_SIZE_OPTIONS,
                    "domLayout": "autoHeight",
                    "suppressColumnVirtualisation": True,  # Show all columns
                },
                theme="quartz",
                auto_size_columns=False,
            ).classes("w-full")

        except Exception as e:
            logger.error(f"Error rendering table {table_id}: {e}", exc_info=True)
            ui.label(f"Error loading table: {str(e)}").classes("text-error p-4")

    render_with_data_loading(
        storage_keys=["assets_sheet", "liabilities_sheet"],
        render_functions=[render_net_worth_chart, render_assets_liabilities_tables],
        error_container=chart_container,
    )
