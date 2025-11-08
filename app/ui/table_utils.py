"""Shared utilities for table rendering and data export.

This module contains reusable components and functions for AG Grid tables,
CSV exports, and related UI elements used across multiple pages.
"""

from datetime import datetime
from io import StringIO

import pandas as pd
from nicegui import ui


def render_mobile_table_message() -> None:
    """Render mobile-only message explaining data tables are hidden.

    Displays a card with icon and text explaining that data tables are only
    visible on desktop and tablet devices, not on mobile.

    This component should be rendered inside a container and is automatically
    hidden on medium+ screen sizes via Tailwind's md:hidden class.

    Example:
        >>> with ui.column():
        >>>     render_mobile_table_message()
    """
    with (
        ui.card()
        .classes(
            "w-full max-w-screen-xl mx-auto p-6 flex items-center justify-center bg-base-100 shadow-md md:hidden"
        )
        .style("min-height: 200px;")
    ):
        with ui.column().classes("items-center gap-3 text-center"):
            ui.icon("table_chart", size="56px").classes("text-base-content/40")
            ui.label("Where's my data table?").classes("text-xl font-semibold text-base-content")
            ui.label("Data tables are visible on desktop and tablet only").classes(
                "text-sm text-base-content/60"
            )


def export_dataframe_to_csv(
    df: pd.DataFrame,
    filename_prefix: str,
    columns_to_drop: list[str] | None = None,
) -> None:
    """Export DataFrame to CSV file with automatic download.

    Creates a CSV export from a DataFrame, optionally dropping specified columns,
    and triggers a browser download with a timestamped filename.

    Args:
        df: DataFrame to export.
        filename_prefix: Prefix for the filename (e.g., "kanso_expenses").
        columns_to_drop: Optional list of column names to exclude from export.

    Example:
        >>> df = pd.DataFrame({"Date": ["2024-01"], "Amount": [100.50]})
        >>> export_dataframe_to_csv(df, "kanso_assets", columns_to_drop=["Date_DT"])
        # Downloads: kanso_assets_20241106_143022.csv
    """
    # Create clean DataFrame for export
    df_export = df.copy()

    # Drop unwanted columns
    if columns_to_drop:
        existing_cols_to_drop = [col for col in columns_to_drop if col in df_export.columns]
        if existing_cols_to_drop:
            df_export = df_export.drop(columns=existing_cols_to_drop)

    # Convert to CSV
    csv_buffer = StringIO()
    df_export.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.csv"

    # Trigger download
    ui.download(csv_content.encode("utf-8"), filename)
    ui.notify("✓ Exported to CSV", type="positive")


def create_csv_export_button(
    df: pd.DataFrame,
    filename_prefix: str,
    columns_to_drop: list[str] | None = None,
) -> ui.button:
    """Create a CSV export button for a DataFrame.

    Args:
        df: DataFrame to export when clicked.
        filename_prefix: Prefix for the filename (e.g., "kanso_expenses").
        columns_to_drop: Optional list of column names to exclude from export.

    Returns:
        Configured button element with export functionality.

    Example:
        >>> df = pd.DataFrame({"Date": ["2024-01"], "Amount": [100.50]})
        >>> button = create_csv_export_button(df, "kanso_assets", ["Date_DT"])
        >>> button.classes("custom-class")  # Can further customize
    """

    def export_csv():
        export_dataframe_to_csv(df, filename_prefix, columns_to_drop)

    return (
        ui.button(icon="download", on_click=export_csv).props("flat dense").tooltip("Export to CSV")
    )
