"""Centralized data loading utilities for UI pages.

This module provides utilities to standardize data loading patterns across pages,
eliminating duplication and ensuring consistent behavior.
"""

from collections.abc import Awaitable, Callable

from nicegui import app, ui

from app.ui.rendering_utils import render_error_message


def render_with_data_loading(
    *,
    storage_keys: list[str],
    render_functions: list[Callable[[], Awaitable[None]]],
    error_container: ui.element,
    background_delay: float = 0.1,
    render_delay: float = 0.5,
) -> None:
    """Render page components with automatic data loading if needed.

    This utility consolidates the common pattern of:
    1. Check if required data is loaded in storage
    2. If not loaded: trigger background loading, then render on success
    3. If already loaded: render immediately with timers

    Args:
        storage_keys: List of app.storage.general keys to check (e.g., ["assets_sheet"])
        render_functions: List of async functions to call for rendering components
        error_container: UI element to show error messages in case of failure
        background_delay: Timer delay (seconds) before starting background loading (default: 0.1)
        render_delay: Timer delay (seconds) before rendering when data already loaded (default: 0.5)

    Example:
        >>> containers = renderer.render_skeleton_ui()
        >>> await render_with_data_loading(
        ...     storage_keys=["expenses_sheet"],
        ...     render_functions=[
        ...         lambda: renderer.render_chart(containers["chart1"]),
        ...         lambda: renderer.render_table(containers["table"]),
        ...     ],
        ...     error_container=containers["table"],
        ... )
    """
    # Check if all required data is loaded
    data_loaded = all(app.storage.general.get(key) for key in storage_keys)

    if not data_loaded:
        # Data not loaded yet - start background loading
        async def load_data_in_background():
            """Load data from Google Sheets in background."""
            from app.services.data_loader import ensure_data_loaded

            try:
                success = await ensure_data_loaded()
                if success:
                    # Data loaded successfully - render all components
                    for render_fn in render_functions:
                        await render_fn()
                else:
                    # Failed to load data - show error
                    render_error_message(
                        error_container,
                        "Failed to load data. Please check your configuration in Advanced Settings.",
                    )
            except Exception as e:
                # Exception during loading - show error
                render_error_message(error_container, f"Error loading data: {str(e)}")

        # Start loading data asynchronously (non-blocking)
        ui.timer(background_delay, load_data_in_background, once=True)
    else:
        # Data already loaded - render components immediately with timers
        for render_fn in render_functions:
            ui.timer(render_delay, render_fn, once=True)
