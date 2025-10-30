"""Reusable skeleton loader components for consistent loading states."""

from nicegui import ui

from app.ui import styles


def render_chart_skeleton(container: ui.element, title_width: str = "w-48") -> None:
    """Render skeleton loaders for a chart card.

    Shows placeholders for:
    - Chart title (customizable width)
    - Chart content (full width, h-96)

    Args:
        container: UI container to render skeleton into
        title_width: Tailwind width class for title skeleton (e.g., "w-48", "w-64")

    Example:
        >>> chart_container = ui.card().classes("chart-card")
        >>> render_chart_skeleton(chart_container, title_width="w-64")
    """
    with container:
        # Title skeleton
        ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
            f"{title_width} h-6 rounded mb-4"
        )
        # Chart skeleton - h-96 for consistent chart height
        ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
            "w-full h-96 rounded-lg"
        )


def render_kpi_card_skeleton(container: ui.element) -> None:
    """Render skeleton loaders for a KPI stat card.

    Shows placeholders for:
    - Label (small text)
    - Value (large prominent number)
    - Description (full-width text)

    Args:
        container: UI container to render skeleton into

    Example:
        >>> kpi_card = ui.card().classes("stat-card")
        >>> render_kpi_card_skeleton(kpi_card)
    """
    with container:
        # Label skeleton (e.g., "Net Worth", "MoM Δ")
        ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
            "w-24 h-4 rounded mb-2"
        )
        # Value skeleton (larger, prominent)
        ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
            "w-32 h-8 rounded mb-2"
        )
        # Description skeleton (full width)
        ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes("w-full h-3 rounded")


def render_table_skeleton(container: ui.element, height: str = "h-96") -> None:
    """Render skeleton loader for a data table.

    Args:
        container: UI container to render skeleton into
        height: Tailwind height class (e.g., "h-96", "h-64")

    Example:
        >>> table_container = ui.column()
        >>> render_table_skeleton(table_container, height="h-96")
    """
    with container:
        ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
            f"w-full {height} rounded-lg"
        )


def render_large_chart_skeleton(container: ui.element, title_width: str = "w-64") -> None:
    """Render skeleton loaders for a large chart card (e.g., full-page visualizations).

    Similar to render_chart_skeleton but optimized for larger charts
    that take up more vertical space.

    Args:
        container: UI container to render skeleton into
        title_width: Tailwind width class for title skeleton

    Example:
        >>> chart_container = ui.card().style("height: 60vh")
        >>> render_large_chart_skeleton(chart_container)
    """
    with container:
        # Title skeleton
        ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
            f"{title_width} h-8 rounded mb-4 ml-4 mt-4"
        )
        # Chart skeleton - flex-grow to fill remaining space
        ui.skeleton(animation_speed=styles.SKELETON_ANIMATION_SPEED).classes(
            "w-full flex-grow rounded-lg mx-4 mb-4"
        )
