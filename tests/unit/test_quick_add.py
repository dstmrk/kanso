"""Unit tests for quick add expense functionality."""

import pandas as pd
import pytest
from nicegui import app

from app.core.constants import COL_CATEGORY, COL_MERCHANT, COL_TYPE
from app.ui.quick_add import get_expense_options


def to_storage_format(data: list[dict]) -> str:
    """Convert list of dicts to pandas split-oriented JSON format for storage."""
    df = pd.DataFrame(data)
    return df.to_json(orient="split")


class TestGetExpenseOptions:
    """Test the get_expense_options function."""

    @pytest.mark.asyncio
    async def test_get_expense_options_with_data(self):
        """Test extracting unique merchants, categories, and types from expenses data."""
        # Prepare sample expenses data
        sample_data = [
            {COL_MERCHANT: "Amazon", COL_CATEGORY: "Shopping", COL_TYPE: "Discretionary"},
            {COL_MERCHANT: "Walmart", COL_CATEGORY: "Food", COL_TYPE: "Essential"},
            {COL_MERCHANT: "Amazon", COL_CATEGORY: "Electronics", COL_TYPE: "Discretionary"},
            {COL_MERCHANT: "Target", COL_CATEGORY: "Food", COL_TYPE: "Essential"},
        ]

        # Store in app.storage.general (using pandas split-oriented format)
        app.storage.general["expenses_sheet"] = to_storage_format(sample_data)

        # Call the function
        merchants, categories, types = await get_expense_options()

        # Verify results (should be sorted and unique)
        assert merchants == ["Amazon", "Target", "Walmart"]
        assert categories == ["Electronics", "Food", "Shopping"]
        assert types == ["Discretionary", "Essential"]

    @pytest.mark.asyncio
    async def test_get_expense_options_empty_data(self):
        """Test with empty expenses sheet."""
        # Store empty list
        app.storage.general["expenses_sheet"] = to_storage_format([])

        # Call the function
        merchants, categories, types = await get_expense_options()

        # Should return empty lists
        assert merchants == []
        assert categories == []
        assert types == []

    @pytest.mark.asyncio
    async def test_get_expense_options_no_data(self):
        """Test when expenses_sheet is not in storage."""
        # Clear storage
        if "expenses_sheet" in app.storage.general:
            del app.storage.general["expenses_sheet"]

        # Call the function
        merchants, categories, types = await get_expense_options()

        # Should return empty lists
        assert merchants == []
        assert categories == []
        assert types == []

    @pytest.mark.asyncio
    async def test_get_expense_options_with_nan_values(self):
        """Test handling of NaN values in data."""
        # Prepare data with some NaN values
        sample_data = [
            {COL_MERCHANT: "Amazon", COL_CATEGORY: "Shopping", COL_TYPE: "Discretionary"},
            {COL_MERCHANT: None, COL_CATEGORY: "Food", COL_TYPE: "Essential"},
            {COL_MERCHANT: "Target", COL_CATEGORY: None, COL_TYPE: "Essential"},
        ]

        app.storage.general["expenses_sheet"] = to_storage_format(sample_data)

        # Call the function
        merchants, categories, types = await get_expense_options()

        # Should exclude NaN values
        assert merchants == ["Amazon", "Target"]
        assert categories == ["Food", "Shopping"]
        assert types == ["Discretionary", "Essential"]

    @pytest.mark.asyncio
    async def test_get_expense_options_sorting(self):
        """Test that results are sorted alphabetically."""
        # Prepare unsorted data
        sample_data = [
            {COL_MERCHANT: "Zebra Store", COL_CATEGORY: "Utilities", COL_TYPE: "Essential"},
            {COL_MERCHANT: "Apple Store", COL_CATEGORY: "Entertainment", COL_TYPE: "Discretionary"},
            {COL_MERCHANT: "Market", COL_CATEGORY: "Food", COL_TYPE: "Essential"},
        ]

        app.storage.general["expenses_sheet"] = to_storage_format(sample_data)

        # Call the function
        merchants, categories, types = await get_expense_options()

        # Verify alphabetical sorting
        assert merchants == sorted(merchants)
        assert categories == sorted(categories)
        assert types == sorted(types)

    @pytest.mark.asyncio
    async def test_get_expense_options_invalid_json(self):
        """Test error handling with invalid JSON data."""
        # Store invalid JSON
        app.storage.general["expenses_sheet"] = "invalid json {["

        # Call the function - should handle gracefully
        merchants, categories, types = await get_expense_options()

        # Should return empty lists on error
        assert merchants == []
        assert categories == []
        assert types == []

    @pytest.mark.asyncio
    async def test_get_expense_options_missing_columns(self):
        """Test handling when expected columns are missing."""
        # Data missing some columns
        sample_data = [
            {"Date": "2024-01-01", "Amount": "100"},  # Missing merchant, category, type
        ]

        app.storage.general["expenses_sheet"] = to_storage_format(sample_data)

        # Call the function - should handle KeyError gracefully
        merchants, categories, types = await get_expense_options()

        # Should return empty lists when columns are missing
        assert merchants == []
        assert categories == []
        assert types == []

    @pytest.mark.asyncio
    async def test_get_expense_options_deduplication(self):
        """Test that duplicate values are removed."""
        # Data with duplicates
        sample_data = [
            {COL_MERCHANT: "Amazon", COL_CATEGORY: "Shopping", COL_TYPE: "Discretionary"},
            {COL_MERCHANT: "Amazon", COL_CATEGORY: "Shopping", COL_TYPE: "Discretionary"},
            {COL_MERCHANT: "Amazon", COL_CATEGORY: "Food", COL_TYPE: "Essential"},
            {COL_MERCHANT: "Target", COL_CATEGORY: "Food", COL_TYPE: "Essential"},
        ]

        app.storage.general["expenses_sheet"] = to_storage_format(sample_data)

        # Call the function
        merchants, categories, types = await get_expense_options()

        # Should have unique values only
        assert merchants == ["Amazon", "Target"]
        assert categories == ["Food", "Shopping"]
        assert types == ["Discretionary", "Essential"]
        # Verify counts
        assert len(merchants) == 2
        assert len(categories) == 2
        assert len(types) == 2
