"""Test income sheet loading with single vs multi-level headers.

This tests the scenario where Google Sheets loads with header=[0,1] but
the user actually has only a single header row.
"""

import pandas as pd
import pytest

from app.logic.finance_calculator import FinanceCalculator


def test_incomes_loaded_as_multiindex_from_single_header():
    """Test when Incomes sheet is loaded as MultiIndex but has single header conceptually.

    This can happen when data_loader loads with header=[0,1] but sheet has:
    Row 0: Date | Salary | Freelance
    Row 1: 2024-01 | 3000 | 1000  ← becomes second level of MultiIndex!

    Result: columns might become ('Date', '2024-01'), ('Salary', '3000'), etc.
    We should extract the MOST SPECIFIC (last) name from the tuple.
    """
    data_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02", "2024-03"] * 4,
            "Net Worth": ["€ 10.000"] * 12,
        }
    )

    # Simulate MultiIndex where second level has data values (edge case)
    incomes_df = pd.DataFrame(
        {
            ("Date", "2024-01"): ["2024-01", "2024-02", "2024-03"] * 4,
            ("Salary", "€ 3.000"): ["€ 3.000"] * 12,
            ("Freelance", "€ 1.000"): ["€ 1.000"] * 12,
        }
    )
    incomes_df.columns = pd.MultiIndex.from_tuples(incomes_df.columns)

    # Expenses covering first 2 months only (for this edge case test)
    expenses_df = pd.DataFrame(
        {
            "Date": ["2024-01"] * 3 + ["2024-02"] * 3,
            "Merchant": ["Store"] * 6,
            "Amount": ["€ 800"] * 6,
            "Category": ["Food", "Transport", "Housing"] * 2,
            "Type": ["Variable"] * 6,
        }
    )

    calculator = FinanceCalculator(data_df, expenses_df=expenses_df, incomes_df=incomes_df)
    cash_flow = calculator.get_cash_flow_last_12_months()

    # With updated logic, we filter out monetary values and extract meaningful names:
    # ('Salary', '€ 3.000') → 'Salary' (filters out '€ 3.000')
    # ('Freelance', '€ 1.000') → 'Freelance' (filters out '€ 1.000')
    # This handles malformed MultiIndex where second row has values instead of headers

    print("Cash flow keys:", cash_flow.keys())

    # Even with malformed structure, we extract the correct source names
    assert "Salary" in cash_flow
    assert "Freelance" in cash_flow
    # Should NOT have monetary values as keys
    assert "€ 3.000" not in cash_flow
    assert "€ 1.000" not in cash_flow


def test_incomes_proper_multiindex():
    """Test with proper 2-row MultiIndex header.

    Row 0: Date | Income   | Income
    Row 1: Date | Salary   | Freelance

    Columns: ('Date', 'Date'), ('Income', 'Salary'), ('Income', 'Freelance')
    Should extract: 'Salary' and 'Freelance' (most specific names)
    """
    data_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02", "2024-03"] * 4,
            "Net Worth": ["€ 10.000"] * 12,
        }
    )

    # Proper MultiIndex structure covering 12 full months
    months = [f"2024-{i:02d}" for i in range(1, 13)]
    incomes_df = pd.DataFrame(
        {
            ("Date", "Date"): months,
            ("Income", "Salary"): ["€ 3.000"] * 12,
            ("Income", "Freelance"): ["€ 1.000"] * 12,
        }
    )
    incomes_df.columns = pd.MultiIndex.from_tuples(incomes_df.columns)

    # Expenses covering all 12 months
    expenses_dates = []
    for month in months:
        expenses_dates.extend([month] * 3)  # 3 transactions per month

    expenses_df = pd.DataFrame(
        {
            "Date": expenses_dates,
            "Merchant": ["Store"] * 36,
            "Amount": ["€ 800"] * 36,
            "Category": ["Food", "Transport", "Housing"] * 12,
            "Type": ["Variable"] * 36,
        }
    )

    calculator = FinanceCalculator(data_df, expenses_df=expenses_df, incomes_df=incomes_df)
    cash_flow = calculator.get_cash_flow_last_12_months()

    print("Cash flow keys:", cash_flow.keys())
    print("Cash flow:", cash_flow)

    # With updated logic (LAST non-empty part), should get:
    # ('Income', 'Salary') → 'Salary'
    # ('Income', 'Freelance') → 'Freelance'

    assert "Salary" in cash_flow, f"Expected 'Salary' in {cash_flow.keys()}"
    assert "Freelance" in cash_flow, f"Expected 'Freelance' in {cash_flow.keys()}"

    # Verify amounts (12 months of data)
    assert cash_flow["Salary"] == pytest.approx(36000.0, rel=0.01)  # 3000*12
    assert cash_flow["Freelance"] == pytest.approx(12000.0, rel=0.01)  # 1000*12
