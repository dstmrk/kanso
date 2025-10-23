"""Test net worth calculation with negative liabilities.

This test verifies that:
1. Liabilities that are already negative in the sheet are handled correctly
2. Net worth is only calculated for dates present in Incomes sheet
"""

import pandas as pd

from app.logic.finance_calculator import FinanceCalculator


def test_net_worth_with_negative_liabilities():
    """Test that liabilities already stored as negative values are handled correctly.

    In the Google Sheets, liabilities are stored as negative values (e.g., -100.000).
    Net Worth should be: Assets + Liabilities (since Liabilities is already negative)
    NOT: Assets - Liabilities (which would give Assets - (-100.000) = Assets + 100.000)
    """
    # Assets sheet
    assets_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02", "2024-03"],
            "Cash": ["€ 10.000", "€ 11.000", "€ 12.000"],
        }
    )

    # Liabilities sheet with NEGATIVE values (as in real Google Sheets)
    liabilities_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02", "2024-03"],
            "Mortgage": ["€ -100.000", "€ -99.000", "€ -98.000"],
        }
    )

    calculator = FinanceCalculator(assets_df=assets_df, liabilities_df=liabilities_df)

    # Get current net worth
    net_worth = calculator.get_current_net_worth()

    # Expected: 12.000 + (-98.000) = -86.000
    # NOT: 12.000 - (-98.000) = 110.000
    expected_net_worth = 12_000 + (-98_000)

    print(f"\nNet worth: {net_worth}")
    print(f"Expected: {expected_net_worth}")

    assert abs(net_worth - expected_net_worth) < 1.0, (
        f"Net worth calculation incorrect. Got {net_worth}, expected {expected_net_worth}. "
        f"Liabilities are already negative in the sheet!"
    )


def test_net_worth_limited_to_incomes_dates():
    """Test that net worth is only calculated for dates present in Incomes sheet.

    Even if Assets and Liabilities have more recent dates, we should only show
    net worth up to the most recent date in the Incomes sheet.
    """
    # Incomes sheet - only goes up to 2024-02
    incomes_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02"],
            "Salary": ["€ 3.000", "€ 3.000"],
        }
    )

    # Assets sheet - has data for 2024-03
    assets_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02", "2024-03"],
            "Cash": ["€ 10.000", "€ 11.000", "€ 12.000"],
        }
    )

    # Liabilities sheet - has data for 2024-03
    liabilities_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02", "2024-03"],
            "Mortgage": ["€ -100.000", "€ -99.000", "€ -98.000"],
        }
    )

    calculator = FinanceCalculator(
        assets_df=assets_df, liabilities_df=liabilities_df, incomes_df=incomes_df
    )

    # Get monthly net worth
    net_worth_chart = calculator.get_monthly_net_worth()

    print(f"\nNet worth dates: {net_worth_chart['dates']}")
    print(f"Net worth values: {net_worth_chart['values']}")

    # Should only have 2 dates (2024-01 and 2024-02), not 3
    assert len(net_worth_chart["dates"]) == 2, (
        f"Net worth should only include dates present in Incomes sheet. "
        f"Expected 2 dates, got {len(net_worth_chart['dates'])}"
    )

    # Last date should be 2024-02, not 2024-03
    assert net_worth_chart["dates"][-1] == "2024-02", (
        f"Last net worth date should be 2024-02 (last income date), "
        f"got {net_worth_chart['dates'][-1]}"
    )


def test_net_worth_with_positive_liabilities():
    """Test backward compatibility: if liabilities are stored as positive, still works."""
    # Assets sheet
    assets_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02"],
            "Cash": ["€ 10.000", "€ 11.000"],
        }
    )

    # Liabilities sheet with POSITIVE values (old format)
    liabilities_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02"],
            "Mortgage": ["€ 100.000", "€ 99.000"],
        }
    )

    calculator = FinanceCalculator(assets_df=assets_df, liabilities_df=liabilities_df)

    net_worth = calculator.get_current_net_worth()

    # Expected: 11.000 - 99.000 = -88.000
    expected_net_worth = 11_000 - 99_000

    assert abs(net_worth - expected_net_worth) < 1.0
