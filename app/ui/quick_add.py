"""Quick add expense page - streamlined expense entry."""

import asyncio
import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
from nicegui import app, ui

from app.core.constants import CACHE_TTL_SECONDS, COL_CATEGORY, COL_MERCHANT, COL_TYPE
from app.core.state_manager import state_manager
from app.services import utils
from app.services.google_sheets import GoogleSheetService
from app.ui import header

logger = logging.getLogger(__name__)


async def get_expense_options() -> tuple[list[str], list[str], list[str]]:
    """Load unique merchants, categories and types from existing expenses data.

    Returns:
        Tuple of (merchants, categories, types) as sorted lists of unique values.
        Returns empty lists if no data available.
    """

    def compute_options() -> tuple[list[str], list[str], list[str]]:
        """Extract unique merchants, categories and types from expenses sheet."""
        expenses_sheet_str = app.storage.general.get("expenses_sheet")
        if not expenses_sheet_str:
            return [], [], []

        try:
            expenses_sheet = utils.read_json(expenses_sheet_str)
            df = pd.DataFrame(expenses_sheet)

            if df.empty:
                return [], [], []

            # Extract unique values and sort alphabetically
            merchants = sorted(df[COL_MERCHANT].dropna().unique().tolist())
            categories = sorted(df[COL_CATEGORY].dropna().unique().tolist())
            types = sorted(df[COL_TYPE].dropna().unique().tolist())

            return merchants, categories, types
        except Exception as e:
            logger.error(f"Error extracting expense options: {e}", exc_info=True)
            return [], [], []

    # Cache with same TTL as expenses data
    result = await state_manager.get_or_compute(
        user_storage_key="expenses_sheet",
        computation_key="expense_options_v2",
        compute_fn=compute_options,
        ttl_seconds=CACHE_TTL_SECONDS,
    )

    return result if result else ([], [], [])


def render() -> None:
    """Render the quick add expense page."""
    header.render()

    # Container for the form (with relative positioning for overlay)
    form_container = ui.column().classes("w-full max-w-md mx-auto p-4 mt-8 space-y-6 relative")

    async def render_form():
        """Render the form with dynamically loaded options."""
        # Load expense options from existing data
        merchants, categories, types = await get_expense_options()

        with form_container:
            # Page title
            ui.label("Add Expense").classes("text-3xl font-bold")
            ui.label("Quickly log a new expense").classes("text-base-content/60")

            # Get current date for defaults
            now = datetime.now()
            current_month = now.month
            current_year = now.year

            # Date section (Month + Year on same row)
            ui.label("Date").classes("text-lg font-semibold mt-4")
            with ui.row().classes("w-full gap-4"):
                month_select = ui.select(
                    options=list(range(1, 13)),
                    value=current_month,
                    label="Month",
                ).classes("flex-1")

                year_select = ui.select(
                    options=[current_year - 1, current_year, current_year + 1],
                    value=current_year,
                    label="Year",
                ).classes("flex-1")

            # Merchant select with autocomplete (loaded from existing data)
            merchant_input = (
                ui.select(
                    options=merchants if merchants else [],
                    label="Merchant",
                    with_input=True,
                    new_value_mode="add",  # Allow custom values to be added
                )
                .classes("w-full")
                .props("outlined")
            )

            # Amount input (no placeholder)
            amount_input = (
                ui.number(label="Amount", format="%.2f", min=0.01)
                .classes("w-full")
                .props("outlined")
            )

            # Category dropdown with custom input (loaded from existing data)
            category_select = (
                ui.select(
                    options=categories if categories else ["Other"],
                    label="Category",
                    with_input=True,
                    new_value_mode="add",  # Allow custom values to be added
                )
                .classes("w-full")
                .props("outlined")
            )

            # Type dropdown with custom input (loaded from existing data)
            type_select = (
                ui.select(
                    options=types if types else ["Essential", "Discretionary"],
                    label="Type",
                    with_input=True,
                    new_value_mode="add",  # Allow custom values to be added
                )
                .classes("w-full")
                .props("outlined")
            )

            # Loading overlay (covers entire form, hidden initially) - defined here to be accessible in submit_expense
            with ui.element("div").classes(
                "absolute inset-0 bg-base-300/40 backdrop-blur-sm flex items-center justify-center z-50 min-h-full"
            ) as loading_overlay:
                with ui.column().classes("items-center gap-4"):
                    ui.spinner(size="xl", color="primary")
                    ui.label("Saving expense...").classes("text-xl font-semibold")
            loading_overlay.set_visibility(False)

            # Submit button
            async def submit_expense():
                """Handle expense submission."""
                # Show loading overlay immediately
                loading_overlay.set_visibility(True)

                # Force UI update to show overlay before proceeding
                # Small delay ensures browser receives and renders the overlay
                await asyncio.sleep(0.05)

                # Validate inputs
                if not merchant_input.value:
                    loading_overlay.set_visibility(False)
                    ui.notify("Please enter a merchant name", type="warning")
                    return

                if not amount_input.value or amount_input.value <= 0:
                    loading_overlay.set_visibility(False)
                    ui.notify("Please enter a valid amount", type="warning")
                    return

                if not category_select.value:
                    loading_overlay.set_visibility(False)
                    ui.notify("Please select or enter a category", type="warning")
                    return

                if not type_select.value:
                    loading_overlay.set_visibility(False)
                    ui.notify("Please select or enter a type", type="warning")
                    return

                # Prepare data for submission
                month = int(month_select.value)
                year = int(year_select.value)
                date_str = f"{year:04d}-{month:02d}-01"
                user_currency = app.storage.general.get("currency", utils.get_user_currency())
                amount_formatted = utils.format_currency(
                    amount_input.value, user_currency, decimals=2
                )

                # Capture values before async work
                merchant = merchant_input.value
                category = category_select.value
                expense_type = type_select.value

                # Get credentials and workbook URL from storage
                custom_creds_json = app.storage.general.get("google_credentials_json")
                custom_url = app.storage.general.get("custom_workbook_url")

                if not custom_creds_json or not custom_url:
                    loading_overlay.set_visibility(False)
                    ui.notify("Configuration missing. Please complete onboarding.", type="negative")
                    return

                # Define the blocking operation to run in thread pool
                def save_to_sheets():
                    """Blocking I/O operation - run in thread pool."""
                    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=True) as tmp:
                        json.dump(json.loads(custom_creds_json), tmp, indent=2)
                        tmp.flush()
                        tmp_path = Path(tmp.name)

                        # Initialize service and append (both blocking operations)
                        sheet_service = GoogleSheetService(tmp_path, custom_url)
                        return sheet_service.append_expense(
                            date=date_str,
                            merchant=merchant,
                            amount=amount_formatted,
                            category=category,
                            expense_type=expense_type,
                        )

                try:
                    # Run blocking I/O in thread pool to avoid blocking the event loop
                    loop = asyncio.get_event_loop()
                    success = await loop.run_in_executor(None, save_to_sheets)

                    if success:
                        # Invalidate expenses cache to force refresh
                        state_manager.invalidate_cache("expenses_sheet")

                        # Success notification
                        ui.notify(
                            f"Spesa di {amount_formatted} presso {merchant_input.value} correttamente registrata",
                            type="positive",
                        )

                        # Wait 1.5 seconds to allow user to read the notification
                        await asyncio.sleep(1.5)

                        # Navigate back (overlay stays visible during redirect)
                        ui.navigate.back()
                    else:
                        # Hide overlay on failure
                        loading_overlay.set_visibility(False)
                        ui.notify("Failed to add expense. Check logs for details.", type="negative")

                except Exception as e:
                    logger.error(f"Error adding expense: {e}", exc_info=True)
                    # Hide overlay on error
                    loading_overlay.set_visibility(False)
                    ui.notify(f"Error: {str(e)}", type="negative")

            with ui.row().classes("w-full gap-4 mt-6"):
                with (
                    ui.element("button")
                    .on("click", lambda: ui.navigate.back())
                    .classes("btn btn-outline btn-error flex-1")
                ):
                    ui.label("Cancel")

                with (
                    ui.element("button")
                    .on("click", submit_expense)
                    .classes("btn bg-secondary hover:bg-secondary/80 text-secondary-content flex-1")
                ):
                    ui.label("Add Expense")

    # Render form asynchronously
    ui.timer(0.01, render_form, once=True)
