"""
Tests for finance_calculator module.

Tests parse_monetary_value() and FinanceCalculator methods.
"""

import pytest
import pandas as pd
from datetime import datetime

from app.logic.finance_calculator import parse_monetary_value, FinanceCalculator
from app.core.constants import (
    COL_DATE, COL_NET_WORTH, COL_INCOME, COL_EXPENSES,
    COL_MONTH, COL_CATEGORY, COL_AMOUNT
)


class TestParseMonetaryValue:
    """Tests for parse_monetary_value function."""

    def test_parse_european_format(self):
        """Test parsing European format: € 1.234,56"""
        assert parse_monetary_value("€ 1.234,56") == 1234.56
        assert parse_monetary_value("€ 1.000,00") == 1000.0
        assert parse_monetary_value("€ 123,45") == 123.45

    def test_parse_us_format(self):
        """Test parsing US format is NOT supported (designed for European only)"""
        # Function removes all dots, then converts commas to dots
        # So "$1,234.56" becomes "1,23456" then "1.23456"
        assert parse_monetary_value("$1,234.56") == 1.23456
        assert parse_monetary_value("$1,000.00") == 1.0
        assert parse_monetary_value("$123.45") == 12345.0

    def test_parse_plain_number(self):
        """Test parsing plain numbers in European format."""
        # European format uses comma for decimals
        assert parse_monetary_value("1234,56") == 1234.56
        assert parse_monetary_value("1000") == 1000.0
        assert parse_monetary_value("0") == 0.0
        # Plain number with dot is treated as thousand separator and removed
        assert parse_monetary_value("1.234") == 1234.0

    def test_parse_with_spaces(self):
        """Test parsing with spaces."""
        assert parse_monetary_value("€ 1 234,56") == 1234.56
        assert parse_monetary_value("  1000  ") == 1000.0

    def test_parse_numeric_types(self):
        """Test parsing numeric types directly."""
        assert parse_monetary_value(1234.56) == 1234.56
        assert parse_monetary_value(1000) == 1000.0
        assert parse_monetary_value(0) == 0.0

    def test_parse_none(self):
        """Test parsing None returns 0.0"""
        assert parse_monetary_value(None) == 0.0

    def test_parse_empty_string(self):
        """Test parsing empty string returns 0.0"""
        assert parse_monetary_value("") == 0.0
        assert parse_monetary_value("   ") == 0.0

    def test_parse_invalid_format(self):
        """Test parsing invalid format returns 0.0"""
        assert parse_monetary_value("abc") == 0.0
        assert parse_monetary_value("€€€") == 0.0
        assert parse_monetary_value("not a number") == 0.0


class TestFinanceCalculator:
    """Tests for FinanceCalculator class."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        data = {
            COL_DATE: ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06',
                      '2024-07', '2024-08', '2024-09', '2024-10', '2024-11', '2024-12',
                      '2025-01'],
            COL_NET_WORTH: ['€ 10.000', '€ 11.000', '€ 12.000', '€ 13.000', '€ 14.000', '€ 15.000',
                           '€ 16.000', '€ 17.000', '€ 18.000', '€ 19.000', '€ 20.000', '€ 21.000',
                           '€ 22.000'],
            COL_INCOME: ['€ 3.000'] * 13,
            COL_EXPENSES: ['€ 2.000'] * 13,
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_expenses(self):
        """Create sample expenses data for testing."""
        data = {
            COL_MONTH: ['2025-01'] * 5,
            COL_CATEGORY: ['Food', 'Transport', 'Housing', 'Entertainment', 'Other'],
            COL_AMOUNT: ['€ 500', '€ 300', '€ 800', '€ 200', '€ 200']
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def calculator(self, sample_data):
        """Create FinanceCalculator instance."""
        return FinanceCalculator(sample_data)

    @pytest.fixture
    def calculator_with_expenses(self, sample_data, sample_expenses):
        """Create FinanceCalculator instance with expenses."""
        return FinanceCalculator(sample_data, expenses_df=sample_expenses)

    def test_get_current_net_worth(self, calculator):
        """Test getting current net worth."""
        net_worth = calculator.get_current_net_worth()
        assert net_worth == 22000.0

    def test_get_last_update_date(self, calculator):
        """Test getting last update date."""
        date = calculator.get_last_update_date()
        assert date == '01-2025'  # MM-YYYY format

    def test_get_month_over_month_variation_percentage(self, calculator):
        """Test getting month-over-month variation percentage."""
        variation = calculator.get_month_over_month_net_worth_variation_percentage()
        # From 21,000 to 22,000 = 1,000 / 21,000 ≈ 0.0476 (4.76%)
        assert abs(variation - 0.047619) < 0.00001

    def test_get_month_over_month_variation_absolute(self, calculator):
        """Test getting month-over-month variation absolute."""
        variation = calculator.get_month_over_month_net_worth_variation_absolute()
        assert variation == 1000.0

    def test_get_year_over_year_variation_percentage(self, calculator):
        """Test getting year-over-year variation percentage."""
        variation = calculator.get_year_over_year_net_worth_variation_percentage()
        # From 10,000 to 22,000 = 12,000 / 10,000 = 1.2 (120%)
        assert variation == 1.2

    def test_get_year_over_year_variation_absolute(self, calculator):
        """Test getting year-over-year variation absolute."""
        variation = calculator.get_year_over_year_net_worth_variation_absolute()
        assert variation == 12000.0

    def test_get_average_saving_ratio_percentage(self, calculator):
        """Test getting average saving ratio percentage."""
        ratio = calculator.get_average_saving_ratio_last_12_months_percentage()
        # Income 3000, Expenses 2000 per month = 1000 savings / 3000 income = 0.333... (33.33%)
        assert abs(ratio - 0.333333) < 0.00001

    def test_get_average_saving_ratio_absolute(self, calculator):
        """Test getting average monthly savings absolute."""
        savings = calculator.get_average_saving_ratio_last_12_months_absolute()
        # (3000 - 2000) * 12 months / 12 = 1000
        assert savings == 1000.0

    def test_get_monthly_net_worth(self, calculator):
        """Test getting monthly net worth data."""
        data = calculator.get_monthly_net_worth()
        assert len(data['dates']) == 13
        assert len(data['values']) == 13
        assert data['dates'][0] == '2024-01'
        assert data['dates'][-1] == '2025-01'
        assert data['values'][0] == 10000.0
        assert data['values'][-1] == 22000.0

    def test_get_cash_flow_last_12_months(self, calculator_with_expenses):
        """Test getting cash flow data."""
        cash_flow = calculator_with_expenses.get_cash_flow_last_12_months()
        assert 'Savings' in cash_flow
        assert 'Expenses' in cash_flow
        # Total expenses from sample_expenses = 500+300+800+200+200 = 2000 (only 1 month)
        assert cash_flow['Expenses'] == 2000.0
        # Income last 12 months = 12 × 3000 = 36000, Expenses (1 month) = 2000
        # Savings = 36000 - 2000 = 34000
        assert cash_flow['Savings'] == 36000.0 - 2000.0

    def test_get_average_expenses_by_category(self, calculator_with_expenses):
        """Test getting average expenses by category."""
        expenses = calculator_with_expenses.get_average_expenses_by_category_last_12_months()
        assert expenses['Food'] == 500.0
        assert expenses['Transport'] == 300.0
        assert expenses['Housing'] == 800.0
        assert expenses['Entertainment'] == 200.0
        assert expenses['Other'] == 200.0

    def test_get_incomes_vs_expenses(self, calculator):
        """Test getting income vs expenses data."""
        data = calculator.get_incomes_vs_expenses()
        assert len(data['dates']) == 12  # Last 12 months
        assert len(data['incomes']) == 12
        assert len(data['expenses']) == 12
        # All incomes should be 3000
        assert all(income == 3000.0 for income in data['incomes'])
        # All expenses should be negative 2000
        assert all(expense == -2000.0 for expense in data['expenses'])

    def test_missing_columns(self):
        """Test behavior with missing required columns."""
        df = pd.DataFrame({COL_DATE: ['2024-01']})
        calc = FinanceCalculator(df)
        # Should return 0.0 when columns are missing
        assert calc.get_current_net_worth() == 0.0

    def test_insufficient_data_for_yoy(self):
        """Test year-over-year with insufficient data."""
        df = pd.DataFrame({
            COL_DATE: ['2024-01', '2024-02'],
            COL_NET_WORTH: ['€ 10.000', '€ 11.000'],
            COL_INCOME: ['€ 3.000'] * 2,
            COL_EXPENSES: ['€ 2.000'] * 2,
        })
        calc = FinanceCalculator(df)
        # Should return 0.0 when not enough data
        assert calc.get_year_over_year_net_worth_variation_percentage() == 0.0
        assert calc.get_year_over_year_net_worth_variation_absolute() == 0.0
