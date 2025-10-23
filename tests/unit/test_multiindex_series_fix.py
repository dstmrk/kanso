"""Test that multi-index DataFrames don't cause Series hashability errors.

This test verifies the fix for the issue where row[COL_DATE_DT] returns a Series
instead of a scalar when DataFrames have multi-index columns, which caused
TypeError: unhashable type: 'Series' when trying to add to a set.
"""

import pandas as pd

from app.logic.finance_calculator import FinanceCalculator


def test_multiindex_assets_dont_cause_series_error():
    """Test that multi-index Assets sheet doesn't cause unhashable Series error."""
    # Create assets with multi-index columns (like real Google Sheets data)
    assets_df = pd.DataFrame(
        {
            ("Date", ""): ["2024-01", "2024-02", "2024-03"],
            ("Bank Account", "Chase"): ["€ 10.000", "€ 10.500", "€ 11.000"],
            ("Investments", "Stocks"): ["€ 5.000", "€ 5.200", "€ 5.400"],
        }
    )

    # Create liabilities with multi-index columns
    liabilities_df = pd.DataFrame(
        {
            ("Date", ""): ["2024-01", "2024-02", "2024-03"],
            ("Mortgage", ""): ["€ 100.000", "€ 99.000", "€ 98.000"],
        }
    )

    # This should not raise "TypeError: unhashable type: 'Series'"
    calculator = FinanceCalculator(assets_df=assets_df, liabilities_df=liabilities_df)

    # Verify net worth calculation works (doesn't raise unhashable Series error)
    net_worth = calculator.get_current_net_worth()

    # Net worth should be: 11,000 + 5,400 - 98,000 = -81,600
    expected_net_worth = 11_000 + 5_400 - 98_000
    assert (
        abs(net_worth - expected_net_worth) < 1.0
    ), f"Expected {expected_net_worth}, got {net_worth}"


def test_multiindex_with_incomes_and_expenses():
    """Test complete flow with all multi-index sheets."""
    # Multi-index Assets
    assets_df = pd.DataFrame(
        {
            ("Date", ""): ["2024-01", "2024-02"],
            ("Cash", "Bank"): ["€ 5.000", "€ 5.500"],
        }
    )

    # Multi-index Liabilities
    liabilities_df = pd.DataFrame(
        {
            ("Date", ""): ["2024-01", "2024-02"],
            ("Loan", ""): ["€ 1.000", "€ 900"],
        }
    )

    # Multi-index Incomes
    incomes_df = pd.DataFrame(
        {
            ("Date", ""): ["2024-01", "2024-02"],
            ("Salary", "Company A"): ["€ 3.000", "€ 3.000"],
        }
    )

    # Regular Expenses (Date column is datetime from Google Sheets)
    expenses_df = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01", "2024-02-01"]),
            "Merchant": ["Store", "Store"],
            "Amount": ["€ 1.500", "€ 1.500"],
            "Category": ["Food", "Food"],
            "Type": ["Variable", "Variable"],
        }
    )

    # Should not raise any errors
    calculator = FinanceCalculator(
        assets_df=assets_df,
        liabilities_df=liabilities_df,
        incomes_df=incomes_df,
        expenses_df=expenses_df,
    )

    # Test all major calculations work
    net_worth = calculator.get_current_net_worth()
    assert net_worth > 0

    saving_ratio = calculator.get_average_saving_ratio_last_12_months_percentage()
    # (3000*2 - 1500*2) / (3000*2) = 3000/6000 = 0.5 (50%)
    assert abs(saving_ratio - 0.5) < 0.01

    # Test chart data doesn't cause errors
    net_worth_chart = calculator.get_monthly_net_worth()
    assert len(net_worth_chart["dates"]) == 2
    assert len(net_worth_chart["values"]) == 2

    income_vs_expenses = calculator.get_incomes_vs_expenses()
    assert len(income_vs_expenses["dates"]) == 2
    assert len(income_vs_expenses["incomes"]) == 2
    assert len(income_vs_expenses["expenses"]) == 2


def test_single_index_still_works():
    """Verify that single-index DataFrames still work correctly."""
    # Single-index Assets (no tuples)
    assets_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02"],
            "Cash": ["€ 5.000", "€ 5.500"],
        }
    )

    # Single-index Liabilities
    liabilities_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02"],
            "Loan": ["€ 1.000", "€ 900"],
        }
    )

    calculator = FinanceCalculator(assets_df=assets_df, liabilities_df=liabilities_df)

    net_worth = calculator.get_current_net_worth()
    # 5500 - 900 = 4600
    assert abs(net_worth - 4600) < 1.0
