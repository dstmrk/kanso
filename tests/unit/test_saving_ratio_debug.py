"""Debug tests for saving ratio calculation.

Test to identify why saving ratio shows 0.0% in production.
"""

import pandas as pd

from app.logic.finance_calculator import FinanceCalculator


def test_saving_ratio_with_minimal_data():
    """Test saving ratio with minimal but realistic data."""
    # Data sheet with just 3 months
    data_df = pd.DataFrame(
        {
            "Date": ["2024-10", "2024-11", "2024-12"],
            "Net_Worth": ["€ 10.000", "€ 11.000", "€ 12.000"],
        }
    )

    # Expenses sheet with detailed transactions for 3 months
    expenses_df = pd.DataFrame(
        {
            "Date": ["2024-10", "2024-10", "2024-11", "2024-11", "2024-12", "2024-12"],
            "Merchant": ["Store A", "Store B"] * 3,
            "Amount": ["€ 1.000", "€ 500"] * 3,  # Total 1500 per month
            "Category": ["Food", "Transport"] * 3,
            "Type": ["Variable", "Variable"] * 3,
        }
    )

    # Incomes sheet with multi-index (like real data)
    incomes_df = pd.DataFrame(
        {
            ("Date", ""): ["2024-10", "2024-11", "2024-12"],
            ("Salary", "Company A"): ["€ 2.000", "€ 2.000", "€ 2.000"],
        }
    )

    calculator = FinanceCalculator(data_df, expenses_df=expenses_df, incomes_df=incomes_df)

    # Test saving ratio
    ratio = calculator.get_average_saving_ratio_last_12_months_percentage()

    # Expected: (2000*3 - 1500*3) / (2000*3) = 1500/6000 = 0.25 (25%)
    print(f"\nSaving ratio: {ratio:.2%}")
    print("Expected: 25.0%")

    assert ratio > 0, f"Saving ratio should be > 0, got {ratio}"
    assert abs(ratio - 0.25) < 0.01, f"Expected ~0.25, got {ratio}"


def test_saving_ratio_with_single_income_column():
    """Test saving ratio when incomes are in single column (fallback mode)."""
    # Data sheet with Income column (old format)
    data_df = pd.DataFrame(
        {
            "Date": ["2024-10", "2024-11", "2024-12"],
            "Net_Worth": ["€ 10.000", "€ 11.000", "€ 12.000"],
            "Income": ["€ 2.000", "€ 2.000", "€ 2.000"],
        }
    )

    # Expenses sheet
    expenses_df = pd.DataFrame(
        {
            "Date": ["2024-10", "2024-10", "2024-11", "2024-11", "2024-12", "2024-12"],
            "Merchant": ["Store A", "Store B"] * 3,
            "Amount": ["€ 1.000", "€ 500"] * 3,
            "Category": ["Food", "Transport"] * 3,
            "Type": ["Variable", "Variable"] * 3,
        }
    )

    calculator = FinanceCalculator(data_df, expenses_df=expenses_df)

    ratio = calculator.get_average_saving_ratio_last_12_months_percentage()

    print(f"\nSaving ratio (fallback mode): {ratio:.2%}")
    print("Expected: 25.0%")

    assert ratio > 0, f"Saving ratio should be > 0, got {ratio}"
    assert abs(ratio - 0.25) < 0.01, f"Expected ~0.25, got {ratio}"


def test_saving_ratio_with_no_expenses():
    """Test saving ratio when Expenses sheet is empty."""
    data_df = pd.DataFrame(
        {
            "Date": ["2024-10", "2024-11", "2024-12"],
            "Net_Worth": ["€ 10.000", "€ 11.000", "€ 12.000"],
            "Income": ["€ 2.000", "€ 2.000", "€ 2.000"],
        }
    )

    # No expenses sheet
    calculator = FinanceCalculator(data_df, expenses_df=None)

    ratio = calculator.get_average_saving_ratio_last_12_months_percentage()

    print(f"\nSaving ratio with no expenses: {ratio:.2%}")
    assert ratio == 0.0, "Should return 0.0 when expenses sheet is missing"


def test_saving_ratio_with_no_income():
    """Test saving ratio when there's no income data."""
    data_df = pd.DataFrame(
        {
            "Date": ["2024-10", "2024-11", "2024-12"],
            "Net_Worth": ["€ 10.000", "€ 11.000", "€ 12.000"],
            # No Income column
        }
    )

    expenses_df = pd.DataFrame(
        {
            "Date": ["2024-10", "2024-11", "2024-12"],
            "Merchant": ["Store"] * 3,
            "Amount": ["€ 1.500"] * 3,
            "Category": ["Food"] * 3,
            "Type": ["Variable"] * 3,
        }
    )

    calculator = FinanceCalculator(data_df, expenses_df=expenses_df)

    ratio = calculator.get_average_saving_ratio_last_12_months_percentage()

    print(f"\nSaving ratio with no income: {ratio:.2%}")
    assert ratio == 0.0, "Should return 0.0 when income is 0"


def test_income_calculation_debug():
    """Debug income calculation to see what's happening."""
    data_df = pd.DataFrame(
        {
            "Date": ["2024-10", "2024-11", "2024-12"],
            "Net_Worth": ["€ 10.000", "€ 11.000", "€ 12.000"],
        }
    )

    expenses_df = pd.DataFrame(
        {
            "Date": ["2024-10", "2024-11", "2024-12"],
            "Merchant": ["Store"] * 3,
            "Amount": ["€ 1.500"] * 3,
            "Category": ["Food"] * 3,
            "Type": ["Variable"] * 3,
        }
    )

    # Multi-index incomes
    incomes_df = pd.DataFrame(
        {
            ("Date", ""): ["2024-10", "2024-11", "2024-12"],
            ("Salary", "Company"): ["€ 2.000", "€ 2.000", "€ 2.000"],
        }
    )

    calculator = FinanceCalculator(data_df, expenses_df=expenses_df, incomes_df=incomes_df)

    # Check processed DataFrames
    print("\n=== DEBUG INFO ===")
    print(
        f"Expenses DF shape: {calculator.processed_expenses_df.shape if calculator.processed_expenses_df is not None else 'None'}"
    )
    print(
        f"Incomes DF shape: {calculator.processed_incomes_df.shape if calculator.processed_incomes_df is not None else 'None'}"
    )

    if calculator.processed_expenses_df is not None:
        print(f"\nExpenses DF columns: {calculator.processed_expenses_df.columns.tolist()}")
        print(
            f"Expenses DF dates: {calculator.processed_expenses_df['date_dt'].tolist() if 'date_dt' in calculator.processed_expenses_df else 'No date_dt'}"
        )

    if calculator.processed_incomes_df is not None:
        print(f"\nIncomes DF columns: {calculator.processed_incomes_df.columns.tolist()}")
        print(
            f"Incomes DF dates: {calculator.processed_incomes_df['date_dt'].tolist() if 'date_dt' in calculator.processed_incomes_df else 'No date_dt'}"
        )

    # Get monthly expenses
    monthly_expenses = calculator._get_monthly_expenses_totals()
    if monthly_expenses is not None:
        print(f"\nMonthly expenses totals:\n{monthly_expenses}")

    # Calculate ratio
    ratio = calculator.get_average_saving_ratio_last_12_months_percentage()
    print(f"\nFinal saving ratio: {ratio:.2%}")
