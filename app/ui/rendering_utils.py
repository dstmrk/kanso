"""Common rendering utilities for UI components.

This module provides reusable functions for common rendering patterns
to reduce code duplication across page renderers.
"""

from nicegui import ui

from app.ui import styles


def render_no_data_message(
    container: ui.element,
    title: str,
    tooltip: str = "",
    message: str = "No data available",
) -> None:
    """Render a 'no data available' message in a cleared container.

    Args:
        container: UI container to render into
        title: Title to display
        tooltip: Optional tooltip text
        message: Message to display (default: "No data available")

    Example:
        >>> render_no_data_message(
        ...     chart_container,
        ...     "Net Worth Evolution",
        ...     "Evolution by Asset / Asset Class"
        ... )
    """
    container.clear()
    with container:
        ui.label(title).classes(styles.CHART_CARDS_LABEL_CLASSES)
        if tooltip:
            ui.tooltip(tooltip)
        ui.label(message).classes("text-center text-gray-500 p-8")


def render_error_message(
    container: ui.element,
    error_text: str,
    is_col_span_full: bool = False,
) -> None:
    """Render an error message in a cleared container.

    Args:
        container: UI container to render into
        error_text: Error message to display
        is_col_span_full: Whether to add col-span-full class (for grid layouts)

    Example:
        >>> render_error_message(
        ...     error_container,
        ...     "Failed to load data. Please check your configuration.",
        ...     is_col_span_full=True
        ... )
    """
    container.clear()
    classes = "text-center text-error text-lg"
    if is_col_span_full:
        classes += " col-span-full"

    with container:
        ui.label(error_text).classes(classes)
