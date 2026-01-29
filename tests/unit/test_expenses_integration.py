"""Integration tests for expenses data handling.

Verifies that Expenses sheet (detailed transactions) is used for all expense calculations,
replacing the deprecated Expenses column from the Data sheet.
"""

import pandas as pd
import pytest

from app.logic.finance_calculator import FinanceCalculator


class TestExpensesIntegration:
    """Test expenses data integration using the detailed Expenses sheet."""

    def test_expenses_sheet_required_for_calculations(self):
        """Test that Expenses sheet is required for all expense calculations."""
        # Incomes data
        incomes_df = pd.DataFrame(
            {
                "Date": ["2024-01", "2024-02", "2024-03"],
                "Salary": ["€ 3.000", "€ 3.000", "€ 3.000"],
            }
        )

        calculator = FinanceCalculator(incomes_df=incomes_df)

        # Without Expenses sheet, all expense calculations should return 0 or empty
        saving_ratio = calculator.get_average_saving_ratio_last_12_months_percentage()
        assert saving_ratio == pytest.approx(0.0)
        income_vs_expenses = calculator.get_incomes_vs_expenses()
        assert len(income_vs_expenses["dates"]) == 0
        assert len(income_vs_expenses["expenses"]) == 0

    def test_expenses_sheet_for_category_breakdown(self):
        """Test that Expenses sheet is used for category breakdown."""
        # Detailed expenses sheet with transactions
        expenses_df = pd.DataFrame(
            {
                "Date": ["2024-01", "2024-01", "2024-01", "2024-02", "2024-02"],
                "Merchant": ["Grocery", "Gas Station", "Rent", "Grocery", "Netflix"],
                "Amount": ["€ 500", "€ 200", "€ 1.000", "€ 550", "€ 15"],
                "Category": ["Food", "Transport", "Housing", "Food", "Entertainment"],
                "Type": ["Variable", "Variable", "Fixed", "Variable", "Fixed"],
            }
        )

        calculator = FinanceCalculator(expenses_df=expenses_df)

        # Should be able to get category breakdown from detailed expenses
        category_totals = calculator.get_average_expenses_by_category_last_12_months()

        assert "Food" in category_totals
        assert "Transport" in category_totals
        assert "Housing" in category_totals
        assert "Entertainment" in category_totals

        # Verify totals are correct (500 + 550 = 1050 for Food)
        assert category_totals["Food"] == pytest.approx(1050.0, rel=0.01)
        assert category_totals["Transport"] == pytest.approx(200.0, rel=0.01)
        assert category_totals["Housing"] == pytest.approx(1000.0, rel=0.01)
        assert category_totals["Entertainment"] == pytest.approx(15.0, rel=0.01)

    def test_expenses_sheet_used_for_all_calculations(self):
        """Test that Expenses sheet is used for all expense-related calculations."""
        # Incomes data
        incomes_df = pd.DataFrame(
            {
                "Date": ["2024-01", "2024-02"],
                "Salary": ["€ 3.000", "€ 3.000"],
            }
        )

        # Detailed expenses sheet with all transactions
        expenses_df = pd.DataFrame(
            {
                "Date": ["2024-01", "2024-01", "2024-02", "2024-02"],
                "Merchant": ["Store A", "Store B", "Store C", "Store D"],
                "Amount": ["€ 1.000", "€ 1.000", "€ 1.050", "€ 1.050"],
                "Category": ["Food", "Housing", "Food", "Transport"],
                "Type": ["Variable", "Fixed", "Variable", "Variable"],
            }
        )

        calculator = FinanceCalculator(expenses_df=expenses_df, incomes_df=incomes_df)

        # All calculations should work using Expenses sheet
        saving_ratio = calculator.get_average_saving_ratio_last_12_months_percentage()
        assert saving_ratio > 0  # (3000*2 - 2000*2) / (3000*2) = 0.33

        category_totals = calculator.get_average_expenses_by_category_last_12_months()
        assert len(category_totals) > 0
        assert "Food" in category_totals
        assert "Housing" in category_totals

        # Income vs expenses should use Expenses sheet totals
        income_vs_expenses = calculator.get_incomes_vs_expenses()
        assert len(income_vs_expenses["dates"]) == 2
        assert len(income_vs_expenses["expenses"]) == 2
        # Expenses are negative for charting
        assert income_vs_expenses["expenses"][0] == -2000.0  # Jan: 1000 + 1000
        assert income_vs_expenses["expenses"][1] == -2100.0  # Feb: 1050 + 1050

    def test_expenses_sheet_new_columns_dont_break_calculations(self):
        """Test that new Merchant and Type columns in Expenses sheet don't break existing calculations."""
        # New 5-column format
        expenses_df = pd.DataFrame(
            {
                "Date": ["2024-01", "2024-01"],
                "Merchant": ["Amazon", "Local Store"],  # NEW COLUMN
                "Amount": ["€ 100", "€ 200"],
                "Category": ["Shopping", "Food"],
                "Type": ["Variable", "Variable"],  # NEW COLUMN
            }
        )

        calculator = FinanceCalculator(expenses_df=expenses_df)

        # Should still work with new columns
        category_totals = calculator.get_average_expenses_by_category_last_12_months()
        assert "Shopping" in category_totals
        assert "Food" in category_totals
        assert category_totals["Shopping"] == pytest.approx(100.0, rel=0.01)
        assert category_totals["Food"] == pytest.approx(200.0, rel=0.01)
