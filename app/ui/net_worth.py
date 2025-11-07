from datetime import datetime
from io import StringIO

import pandas as pd
from nicegui import ui

from app.core.constants import CACHE_TTL_SHORT_SECONDS, COL_DATE, COL_DATE_DT
from app.core.state_manager import state_manager
from app.logic.monetary_parsing import parse_monetary_value
from app.services.finance_service import FinanceService
from app.ui import charts, header
from app.ui.common import get_user_preferences
from app.ui.components.skeleton import render_large_chart_skeleton, render_table_skeleton
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


async def load_assets_liabilities_data() -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """Load assets and liabilities DataFrames, filtered to valid dates.

    Uses the same date filtering logic as the net worth chart: only shows dates
    up to the most recent date in the Incomes sheet (no future dates).

    Returns:
        Tuple of (assets_df, liabilities_df), either can be None if no data
    """
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


def build_aggrid_columns_from_dataframe(df: pd.DataFrame) -> list[dict]:
    """Build AG Grid columnDefs dynamically from DataFrame with multi-level header support.

    Supports both single-level columns (str) and multi-level columns (tuple).
    Multi-level columns are grouped under their category (first level).

    Args:
        df: DataFrame with single or multi-level columns

    Returns:
        List of AG Grid column definitions with groups for multi-level headers

    Example:
        Single-level: ["Date", "Cash", "Savings"] → 3 columns
        Multi-level: [("Date", ""), ("Cash", "Checking"), ("Cash", "Savings")]
                   → Date column + Cash group with 2 children
    """
    # Date column always first, pinned, sorted descending
    column_defs: list[dict] = [
        {
            "field": "Date",
            "headerName": "Date",
            "sortable": True,
            "sort": "desc",
            "pinned": "left",
            "minWidth": 100,
            "width": 110,
        }
    ]

    # Group columns by category (for multi-level) or individual (for single-level)
    column_groups: dict[str, list[tuple[str | None, str]]] = {}

    for col in df.columns:
        # Skip date columns (both original and computed)
        if col == COL_DATE_DT or col == COL_DATE:
            continue
        if isinstance(col, tuple) and (COL_DATE in col or COL_DATE_DT in col):
            continue

        if isinstance(col, tuple) and len(col) == 2:
            # Multi-level: (category, item)
            category, item = col[0].strip(), col[1].strip()
            if not category or not item:
                continue
            if category not in column_groups:
                column_groups[category] = []
            column_groups[category].append((category, item))
        else:
            # Single-level: treat as standalone column
            item = str(col)
            if item not in column_groups:
                column_groups[item] = []
            column_groups[item].append((None, item))

    # Build column definitions from groups
    for category, items in column_groups.items():
        if len(items) == 1 and items[0][0] is None:
            # Single-level column: no grouping needed
            item = items[0][1]
            column_defs.append(
                {
                    "field": item,
                    "headerName": item,
                    "sortable": True,
                    "type": "rightAligned",
                    "valueFormatter": "value != null ? value.toLocaleString('de-DE', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' €' : '0,00 €'",
                    "minWidth": 120,
                    "flex": 1,
                }
            )
        else:
            # Multi-level: create column group with children
            children = []
            for cat, item in items:
                # Create field name: Category_Item (internal identifier)
                field_name = f"{cat}_{item}".replace(" ", "_")
                children.append(
                    {
                        "field": field_name,
                        "headerName": item,  # User sees only item name
                        "sortable": True,
                        "type": "rightAligned",
                        "valueFormatter": "value != null ? value.toLocaleString('de-DE', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' €' : '0,00 €'",
                        "minWidth": 120,
                        "flex": 1,
                    }
                )

            column_defs.append(
                {
                    "headerName": category,  # Group header
                    "children": children,
                }
            )

    return column_defs


def prepare_dataframe_for_aggrid(df: pd.DataFrame) -> list[dict]:
    """Prepare DataFrame rows for AG Grid with flattened column names.

    Converts DataFrame to list of dictionaries, flattening multi-level columns
    to match the field names in columnDefs (Category_Item format).

    Args:
        df: DataFrame with single or multi-level columns

    Returns:
        List of row dictionaries ready for AG Grid rowData
    """
    rows = []

    # Convert DataFrame to list of dicts (handles multi-index automatically)
    df_records = df.to_dict("records")

    for record in df_records:
        row_dict: dict[str, str | float] = {}

        # Extract and format date
        date_value = None
        if COL_DATE_DT in record:
            date_value = record[COL_DATE_DT]
        else:
            # Try to find Date in record keys (for multi-index)
            for key in record:
                if isinstance(key, tuple) and COL_DATE in key:
                    date_value = record[key]
                    break
                elif key == COL_DATE:
                    date_value = record[key]
                    break

        # Format date value
        if date_value is not None and not pd.isna(date_value):
            if isinstance(date_value, (pd.Timestamp, datetime)):
                row_dict["Date"] = date_value.strftime("%Y-%m")
            else:
                try:
                    row_dict["Date"] = pd.to_datetime(date_value).strftime("%Y-%m")
                except Exception:
                    row_dict["Date"] = str(date_value)
        else:
            row_dict["Date"] = ""

        # Process all other columns
        for col_key, value in record.items():
            # Skip date columns (already handled)
            if col_key == COL_DATE_DT or col_key == COL_DATE:
                continue
            if isinstance(col_key, tuple) and (COL_DATE in col_key or COL_DATE_DT in col_key):
                continue

            # Parse monetary value using the same parser as finance_calculator
            parsed_value = parse_monetary_value(value)
            if parsed_value is None:
                parsed_value = 0.0

            # Create field name matching columnDefs
            if isinstance(col_key, tuple) and len(col_key) == 2:
                # Multi-level: flatten to Category_Item
                category, item = col_key[0].strip(), col_key[1].strip()
                field_name = f"{category}_{item}".replace(" ", "_")
            else:
                # Single-level: use column name as-is
                field_name = str(col_key)

            row_dict[field_name] = parsed_value

        rows.append(row_dict)

    return rows


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

        # Data tables in tabs (hidden on mobile)
        with ui.card().classes(
            "max-md:hidden w-full max-w-screen-xl mx-auto bg-base-100 shadow-md"
        ):
            with ui.tabs().classes("w-full") as tabs:
                assets_tab = ui.tab("Assets")
                liabilities_tab = ui.tab("Liabilities")

            with (
                ui.tab_panels(tabs, value=assets_tab).classes("w-full").style("overflow: visible;")
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
            df: DataFrame to display
            table_id: Unique ID for this table instance (e.g., "assets_table")
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Export button only
            with ui.row().classes("w-full justify-end items-center mb-4 px-4 pt-4"):
                # CSV Export button
                def export_csv():
                    """Export table data to CSV file."""
                    # Create clean DataFrame for export
                    df_export = df.copy()

                    # Drop internal columns
                    columns_to_drop = [col for col in df_export.columns if col == COL_DATE_DT]
                    if columns_to_drop:
                        df_export = df_export.drop(columns=columns_to_drop)

                    # Convert to CSV
                    csv_buffer = StringIO()
                    df_export.to_csv(csv_buffer, index=False)
                    csv_content = csv_buffer.getvalue()

                    # Generate filename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"kanso_{table_id}_{timestamp}.csv"

                    # Trigger download
                    ui.download(csv_content.encode("utf-8"), filename)
                    ui.notify("✓ Exported to CSV", type="positive")

                ui.button(icon="download", on_click=export_csv).props("flat dense").tooltip(
                    "Export to CSV"
                )

            # Build AG Grid columns and rows
            column_defs = build_aggrid_columns_from_dataframe(df)
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
                    "paginationPageSize": 25,
                    "paginationPageSizeSelector": [10, 25],
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
