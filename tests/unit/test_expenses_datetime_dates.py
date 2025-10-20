"""Test expenses with datetime Date column (as from Google Sheets).

When loading data from Google Sheets, pandas automatically converts date strings
to datetime objects. This test verifies that the finance calculator handles this
correctly.
"""

import pandas as pd
import pytest

from app.logic.finance_calculator import FinanceCalculator


def test_expenses_with_datetime_dates():
    """Test that expenses work when Date column contains datetime objects."""
    # Main data sheet
    data_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02", "2024-03"],
            "Net_Worth": ["€ 10.000", "€ 11.000", "€ 12.000"],
            "Income": ["€ 3.000", "€ 3.000", "€ 3.000"],
        }
    )

    # Expenses sheet with datetime Date column (as loaded from Google Sheets)
    expenses_df = pd.DataFrame(
        {
            "Date": pd.to_datetime(
                ["2024-01-01", "2024-01-01", "2024-02-01", "2024-02-01", "2024-03-01", "2024-03-01"]
            ),
            "Merchant": ["Store A", "Store B"] * 3,
            "Amount": ["€ 1.000", "€ 500"] * 3,  # Total 1500 per month
            "Category": ["Food", "Transport"] * 3,
            "Type": ["Variable", "Variable"] * 3,
        }
    )

    # Verify Date column is datetime dtype
    assert pd.api.types.is_datetime64_any_dtype(expenses_df["Date"])

    calculator = FinanceCalculator(data_df, expenses_df=expenses_df)

    # Test saving ratio
    ratio = calculator.get_average_saving_ratio_last_12_months_percentage()
    # Expected: (3000*3 - 1500*3) / (3000*3) = 4500/9000 = 0.5 (50%)
    assert ratio > 0, f"Saving ratio should be > 0, got {ratio}"
    assert abs(ratio - 0.5) < 0.01, f"Expected ~0.5, got {ratio}"

    # Test income vs expenses
    income_vs_expenses = calculator.get_incomes_vs_expenses()
    assert len(income_vs_expenses["dates"]) == 3
    assert len(income_vs_expenses["expenses"]) == 3
    assert income_vs_expenses["expenses"][0] == -1500.0  # Jan
    assert income_vs_expenses["expenses"][1] == -1500.0  # Feb
    assert income_vs_expenses["expenses"][2] == -1500.0  # Mar

    # Test category breakdown
    category_totals = calculator.get_average_expenses_by_category_last_12_months()
    assert "Food" in category_totals
    assert "Transport" in category_totals
    # Total across 3 months: 1000 * 3 = 3000, 500 * 3 = 1500
    assert category_totals["Food"] == pytest.approx(3000.0, rel=0.01)
    assert category_totals["Transport"] == pytest.approx(1500.0, rel=0.01)


def test_expenses_with_mixed_date_formats():
    """Test that calculator handles both string and datetime dates."""
    # Main data with string dates
    data_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02"],
            "Net_Worth": ["€ 10.000", "€ 11.000"],
            "Income": ["€ 3.000", "€ 3.000"],
        }
    )

    # Expenses with datetime dates (from Google Sheets)
    expenses_df_datetime = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01", "2024-02-01"]),
            "Merchant": ["Store", "Store"],
            "Amount": ["€ 1.500", "€ 1.500"],
            "Category": ["Food", "Food"],
            "Type": ["Variable", "Variable"],
        }
    )

    calculator = FinanceCalculator(data_df, expenses_df=expenses_df_datetime)
    ratio = calculator.get_average_saving_ratio_last_12_months_percentage()

    # (3000*2 - 1500*2) / (3000*2) = 3000/6000 = 0.5 (50%)
    assert abs(ratio - 0.5) < 0.01


def test_expenses_datetime_dates_are_normalized_to_month():
    """Test that datetime dates on different days of month are normalized correctly."""
    data_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02"],
            "Net_Worth": ["€ 10.000", "€ 11.000"],
        }
    )

    # Expenses on different days of the same month should be grouped together
    expenses_df = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-05", "2024-01-15", "2024-01-25", "2024-02-03"]),
            "Merchant": ["A", "B", "C", "D"],
            "Amount": ["€ 100", "€ 200", "€ 300", "€ 400"],
            "Category": ["Food"] * 4,
            "Type": ["Variable"] * 4,
        }
    )

    calculator = FinanceCalculator(data_df, expenses_df=expenses_df)

    # Get monthly totals
    income_vs_expenses = calculator.get_incomes_vs_expenses()

    # All Jan expenses (5th, 15th, 25th) should be grouped: 100+200+300 = 600
    # Feb expense (3rd) should be: 400
    # Note: expenses are negative in the chart
    assert (
        len([e for e in income_vs_expenses["expenses"] if e == -600.0]) >= 1
    ), "Jan expenses should total 600"
    assert (
        len([e for e in income_vs_expenses["expenses"] if e == -400.0]) >= 1
    ), "Feb expenses should total 400"
