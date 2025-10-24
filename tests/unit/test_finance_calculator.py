"""
Tests for finance_calculator module.

Tests parse_monetary_value() and FinanceCalculator methods.
"""

import pandas as pd
import pytest

from app.core.constants import (
    COL_AMOUNT,
    COL_CATEGORY,
    COL_DATE,
    COL_MERCHANT,
    COL_TYPE,
)
from app.logic.finance_calculator import FinanceCalculator
from app.logic.monetary_parsing import detect_currency, parse_monetary_value


class TestDetectCurrency:
    """Tests for detect_currency function."""

    def test_detect_eur(self):
        """Test detecting EUR from € symbol."""
        assert detect_currency("€ 100") == "EUR"
        assert detect_currency("100 €") == "EUR"

    def test_detect_usd(self):
        """Test detecting USD from $ symbol."""
        assert detect_currency("$100") == "USD"
        assert detect_currency("100 $") == "USD"

    def test_detect_gbp(self):
        """Test detecting GBP from £ symbol."""
        assert detect_currency("£100") == "GBP"
        assert detect_currency("100 £") == "GBP"

    def test_detect_chf(self):
        """Test detecting CHF from Fr or CHF."""
        assert detect_currency("Fr 100") == "CHF"
        assert detect_currency("CHF 100") == "CHF"

    def test_detect_jpy(self):
        """Test detecting JPY from ¥ or JPY."""
        assert detect_currency("¥100") == "JPY"
        assert detect_currency("JPY 100") == "JPY"

    def test_detect_none(self):
        """Test no currency symbol returns None."""
        assert detect_currency("1234.56") is None
        assert detect_currency("abc") is None


class TestParseMonetaryValue:
    """Tests for parse_monetary_value function."""

    def test_parse_european_format(self):
        """Test parsing European format: € 1.234,56"""
        assert parse_monetary_value("€ 1.234,56") == 1234.56
        assert parse_monetary_value("€ 1.000,00") == 1000.0
        assert parse_monetary_value("€ 123,45") == 123.45

    def test_parse_us_format(self):
        """Test parsing US format: $1,234.56"""
        # Now correctly parsed with intelligent detection
        assert parse_monetary_value("$1,234.56") == 1234.56
        assert parse_monetary_value("$1,000.00") == 1000.0
        assert parse_monetary_value("$123.45") == 123.45

    def test_parse_gbp_format(self):
        """Test parsing GBP format: £1,234.56"""
        assert parse_monetary_value("£1,234.56") == 1234.56
        assert parse_monetary_value("£1,000.00") == 1000.0
        assert parse_monetary_value("£123.45") == 123.45

    def test_parse_chf_format(self):
        """Test parsing CHF format: Fr 1.234,56"""
        assert parse_monetary_value("Fr 1.234,56") == 1234.56
        assert parse_monetary_value("CHF 1.000,00") == 1000.0
        assert parse_monetary_value("Fr 123,45") == 123.45

    def test_parse_jpy_format(self):
        """Test parsing JPY format (no decimals): ¥1,234"""
        assert parse_monetary_value("¥1,234") == 1234.0
        assert parse_monetary_value("JPY 1,000") == 1000.0
        assert parse_monetary_value("¥123") == 123.0

    def test_parse_plain_number(self):
        """Test parsing plain numbers without currency symbols."""
        # Plain numbers without separators
        assert parse_monetary_value("1234.56") == 1234.56
        assert parse_monetary_value("1000") == 1000.0
        assert parse_monetary_value("0") == 0.0

    def test_parse_with_spaces(self):
        """Test parsing with spaces."""
        assert parse_monetary_value("€ 1 234,56") == 1234.56
        assert parse_monetary_value("$ 1 234.56") == 1234.56
        assert parse_monetary_value("  1000  ") == 1000.0

    def test_parse_currency_override(self):
        """Test parsing with explicit currency parameter."""
        # Force EUR interpretation on plain number
        assert parse_monetary_value("1.234,56", currency="EUR") == 1234.56
        # Force USD interpretation on plain number
        assert parse_monetary_value("1,234.56", currency="USD") == 1234.56
        # Override detected currency
        assert parse_monetary_value("€ 1,234.56", currency="USD") == 1234.56

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

    def test_parse_mixed_formats(self):
        """Test parsing with different separators."""
        # EUR with thousands
        assert parse_monetary_value("€ 10.000,00") == 10000.0
        # USD with thousands
        assert parse_monetary_value("$10,000.00") == 10000.0
        # JPY with thousands (no decimals)
        assert parse_monetary_value("¥10,000") == 10000.0


class TestFinanceCalculator:
    """Tests for FinanceCalculator class."""

    @pytest.fixture
    def sample_assets(self):
        """Create sample assets data for testing.

        Assets grow from 110k to 122k over 13 months.
        Combined with sample_liabilities (fixed at 100k), this creates
        Net Worth from 10k to 22k.
        """
        data = {
            COL_DATE: [
                "2024-01",
                "2024-02",
                "2024-03",
                "2024-04",
                "2024-05",
                "2024-06",
                "2024-07",
                "2024-08",
                "2024-09",
                "2024-10",
                "2024-11",
                "2024-12",
                "2025-01",
            ],
            "Cash": ["€ 50.000"] * 13,  # Fixed
            "Stocks": [f"€ {60000 + i * 1000}" for i in range(13)],  # Growing: 60k to 72k
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_liabilities(self):
        """Create sample liabilities data for testing.

        Fixed mortgage at 100k throughout all months.
        """
        data = {
            COL_DATE: [
                "2024-01",
                "2024-02",
                "2024-03",
                "2024-04",
                "2024-05",
                "2024-06",
                "2024-07",
                "2024-08",
                "2024-09",
                "2024-10",
                "2024-11",
                "2024-12",
                "2025-01",
            ],
            "Mortgage": ["€ 100.000"] * 13,
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_expenses(self):
        """Create sample detailed expenses data for testing (last month only)."""
        data = {
            COL_DATE: ["2025-01"] * 5,
            COL_MERCHANT: ["Grocery Store", "Gas Station", "Landlord", "Cinema", "Other Store"],
            COL_AMOUNT: ["€ 500", "€ 300", "€ 800", "€ 200", "€ 200"],
            COL_CATEGORY: ["Food", "Transport", "Housing", "Entertainment", "Other"],
            COL_TYPE: ["Variable", "Variable", "Fixed", "Variable", "Variable"],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_detailed_expenses(self):
        """Create detailed expenses data for all 13 months (€2000 per month total)."""
        # Create 13 months of detailed expense transactions
        # Each month has 2 transactions totaling €2000
        months = [
            "2024-01",
            "2024-02",
            "2024-03",
            "2024-04",
            "2024-05",
            "2024-06",
            "2024-07",
            "2024-08",
            "2024-09",
            "2024-10",
            "2024-11",
            "2024-12",
            "2025-01",
        ]
        data = {
            COL_DATE: [],
            COL_MERCHANT: [],
            COL_AMOUNT: [],
            COL_CATEGORY: [],
            COL_TYPE: [],
        }
        for month in months:
            # Two transactions per month totaling €2000
            data[COL_DATE].extend([month, month])
            data[COL_MERCHANT].extend(["Store A", "Store B"])
            data[COL_AMOUNT].extend(["€ 1.200", "€ 800"])
            data[COL_CATEGORY].extend(["Food", "Housing"])
            data[COL_TYPE].extend(["Variable", "Fixed"])
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_incomes(self):
        """Create sample incomes data for all 13 months (€3000 per month total)."""
        data = {
            COL_DATE: [
                "2024-01",
                "2024-02",
                "2024-03",
                "2024-04",
                "2024-05",
                "2024-06",
                "2024-07",
                "2024-08",
                "2024-09",
                "2024-10",
                "2024-11",
                "2024-12",
                "2025-01",
            ],
            "Salary": ["€ 3.000"] * 13,
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def calculator(
        self, sample_assets, sample_liabilities, sample_detailed_expenses, sample_incomes
    ):
        """Create FinanceCalculator instance with assets, liabilities, detailed expenses, and incomes."""
        return FinanceCalculator(
            assets_df=sample_assets,
            liabilities_df=sample_liabilities,
            expenses_df=sample_detailed_expenses,
            incomes_df=sample_incomes,
        )

    @pytest.fixture
    def calculator_with_expenses(
        self, sample_assets, sample_liabilities, sample_expenses, sample_incomes
    ):
        """Create FinanceCalculator instance with assets, liabilities, expenses, and incomes."""
        return FinanceCalculator(
            assets_df=sample_assets,
            liabilities_df=sample_liabilities,
            expenses_df=sample_expenses,
            incomes_df=sample_incomes,
        )

    def test_get_current_net_worth(self, calculator):
        """Test getting current net worth."""
        net_worth = calculator.get_current_net_worth()
        assert net_worth == 22000.0

    def test_get_last_update_date(self, calculator):
        """Test getting last update date."""
        date = calculator.get_last_update_date()
        assert date == "01-2025"  # MM-YYYY format

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
        assert len(data["dates"]) == 13
        assert len(data["values"]) == 13
        assert data["dates"][0] == "2024-01"
        assert data["dates"][-1] == "2025-01"
        assert data["values"][0] == 10000.0
        assert data["values"][-1] == 22000.0

    def test_get_cash_flow_last_12_months(self, calculator_with_expenses):
        """Test getting cash flow data."""
        cash_flow = calculator_with_expenses.get_cash_flow_last_12_months()
        assert "Savings" in cash_flow
        assert "Expenses" in cash_flow
        # Total expenses from sample_expenses = 500+300+800+200+200 = 2000 (only 1 month)
        assert cash_flow["Expenses"] == 2000.0
        # Income last 12 months = 12 × 3000 = 36000, Expenses (1 month) = 2000
        # Savings = 36000 - 2000 = 34000
        assert cash_flow["Savings"] == 36000.0 - 2000.0

    def test_get_average_expenses_by_category(self, calculator_with_expenses):
        """Test getting average expenses by category."""
        expenses = calculator_with_expenses.get_average_expenses_by_category_last_12_months()
        assert expenses["Food"] == 500.0
        assert expenses["Transport"] == 300.0
        assert expenses["Housing"] == 800.0
        assert expenses["Entertainment"] == 200.0
        assert expenses["Other"] == 200.0

    def test_get_incomes_vs_expenses(self, calculator):
        """Test getting income vs expenses data."""
        data = calculator.get_incomes_vs_expenses()
        assert len(data["dates"]) == 12  # Last 12 months
        assert len(data["incomes"]) == 12
        assert len(data["expenses"]) == 12
        # All incomes should be 3000
        assert all(income == 3000.0 for income in data["incomes"])
        # All expenses should be negative 2000
        assert all(expense == -2000.0 for expense in data["expenses"])

    def test_missing_columns(self):
        """Test behavior when no assets/liabilities are provided."""
        # No assets or liabilities provided
        calc = FinanceCalculator()
        # Should return 0.0 when no data available
        assert calc.get_current_net_worth() == 0.0

    def test_insufficient_data_for_yoy(self):
        """Test year-over-year with insufficient data (less than 13 months)."""
        # Create assets and liabilities with only 2 months (insufficient for YoY)
        assets = pd.DataFrame(
            {
                COL_DATE: ["2024-01", "2024-02"],
                "Cash": ["€ 60.000", "€ 61.000"],
            }
        )
        liabilities = pd.DataFrame(
            {
                COL_DATE: ["2024-01", "2024-02"],
                "Mortgage": ["€ 50.000", "€ 50.000"],
            }
        )
        calc = FinanceCalculator(assets_df=assets, liabilities_df=liabilities)
        # Should return 0.0 when not enough data (< 13 months)
        assert calc.get_year_over_year_net_worth_variation_percentage() == 0.0
        assert calc.get_year_over_year_net_worth_variation_absolute() == 0.0
