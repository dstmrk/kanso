"""
Tests for DataFrame structures with single-index and multi-index columns.

This module tests that Assets, Liabilities, and Incomes DataFrames are correctly
parsed from Google Sheets data in both single-index and multi-index formats.
"""

import pandas as pd
import pytest

from app.logic.finance_calculator import FinanceCalculator, parse_monetary_value


class TestAssetsDataFrameStructure:
    """Tests for Assets DataFrame with single and multi-index columns."""

    @pytest.fixture
    def assets_single_index_data(self):
        """Create mock Assets data with single-index columns (employee scenario)."""
        # Simulates Google Sheets structure:
        # Date    | Cash      | Stocks    | Real Estate
        # 2024-01 | € 5.000   | € 10.000  | € 200.000
        # 2024-02 | € 6.000   | € 11.000  | € 200.000
        data = {
            "Date": ["2024-01", "2024-02", "2024-03"],
            "Cash": ["€ 5.000,00", "€ 6.000,00", "€ 7.000,00"],
            "Stocks": ["€ 10.000,00", "€ 11.000,00", "€ 12.000,00"],
            "Real Estate": ["€ 200.000,00", "€ 200.000,00", "€ 200.000,00"],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def assets_multi_index_data(self):
        """Create mock Assets data with multi-index columns (advanced scenario)."""
        # Simulates Google Sheets structure:
        #             Liquid          Investments         Real Estate
        # Date    | Cash | Savings | Stocks | Bonds | Primary | Rental
        # 2024-01 | 5k   | 10k     | 50k    | 20k   | 200k    | 150k
        columns = pd.MultiIndex.from_tuples(
            [
                ("Liquid", "Cash"),
                ("Liquid", "Savings"),
                ("Investments", "Stocks"),
                ("Investments", "Bonds"),
                ("Real Estate", "Primary"),
                ("Real Estate", "Rental"),
            ]
        )
        data = [
            [
                "€ 5.000,00",
                "€ 10.000,00",
                "€ 50.000,00",
                "€ 20.000,00",
                "€ 200.000,00",
                "€ 150.000,00",
            ],
            [
                "€ 6.000,00",
                "€ 11.000,00",
                "€ 55.000,00",
                "€ 21.000,00",
                "€ 200.000,00",
                "€ 150.000,00",
            ],
            [
                "€ 7.000,00",
                "€ 12.000,00",
                "€ 60.000,00",
                "€ 22.000,00",
                "€ 200.000,00",
                "€ 150.000,00",
            ],
        ]
        df = pd.DataFrame(data, columns=columns)
        df.insert(0, ("Date", ""), ["2024-01", "2024-02", "2024-03"])
        return df

    def test_assets_single_index_structure(self, assets_single_index_data):
        """Test that single-index Assets DataFrame is correctly structured."""
        df = assets_single_index_data

        # Verify columns exist
        assert "Date" in df.columns
        assert "Cash" in df.columns
        assert "Stocks" in df.columns
        assert "Real Estate" in df.columns

        # Verify data can be parsed
        assert parse_monetary_value(df["Cash"].iloc[0]) == pytest.approx(5000.0)
        assert parse_monetary_value(df["Stocks"].iloc[1]) == pytest.approx(11000.0)
        assert parse_monetary_value(df["Real Estate"].iloc[2]) == pytest.approx(200000.0)

    def test_assets_multi_index_structure(self, assets_multi_index_data):
        """Test that multi-index Assets DataFrame is correctly structured."""
        df = assets_multi_index_data

        # Verify MultiIndex structure
        assert isinstance(df.columns, pd.MultiIndex)
        assert df.columns.nlevels == 2

        # Verify specific columns exist
        assert ("Liquid", "Cash") in df.columns
        assert ("Investments", "Stocks") in df.columns
        assert ("Real Estate", "Primary") in df.columns

        # Verify data can be parsed
        assert parse_monetary_value(df[("Liquid", "Cash")].iloc[0]) == pytest.approx(5000.0)
        assert parse_monetary_value(df[("Investments", "Stocks")].iloc[1]) == pytest.approx(55000.0)
        assert parse_monetary_value(df[("Real Estate", "Rental")].iloc[2]) == pytest.approx(
            150000.0
        )

    def test_assets_single_index_with_calculator(self, assets_single_index_data):
        """Test FinanceCalculator with single-index Assets DataFrame."""
        calc = FinanceCalculator(assets_df=assets_single_index_data)
        assets_liabilities = calc.get_assets_liabilities()

        # Verify Assets category exists
        assert "Assets" in assets_liabilities
        assert len(assets_liabilities["Assets"]) > 0

    def test_assets_multi_index_with_calculator(self, assets_multi_index_data):
        """Test FinanceCalculator with multi-index Assets DataFrame."""
        calc = FinanceCalculator(assets_df=assets_multi_index_data)
        assets_liabilities = calc.get_assets_liabilities()

        # Verify Assets category exists
        assert "Assets" in assets_liabilities
        # With multi-index, we should have nested categories
        assert "Liquid" in assets_liabilities["Assets"]
        assert "Investments" in assets_liabilities["Assets"]


class TestLiabilitiesDataFrameStructure:
    """Tests for Liabilities DataFrame with single and multi-index columns."""

    @pytest.fixture
    def liabilities_single_index_data(self):
        """Create mock Liabilities data with single-index columns."""
        # Simulates Google Sheets structure:
        # Date    | Mortgage  | Car Loan
        # 2024-01 | € 180.000 | € 5.000
        # 2024-02 | € 179.000 | € 4.500
        data = {
            "Date": ["2024-01", "2024-02", "2024-03"],
            "Mortgage": ["€ 180.000,00", "€ 179.000,00", "€ 178.000,00"],
            "Car Loan": ["€ 5.000,00", "€ 4.500,00", "€ 4.000,00"],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def liabilities_multi_index_data(self):
        """Create mock Liabilities data with multi-index columns."""
        # Simulates Google Sheets structure:
        #             Secured         Unsecured
        # Date    | Mortgage | HELOC | Credit Card | Personal Loan
        # 2024-01 | 180k     | 20k   | 2k          | 5k
        columns = pd.MultiIndex.from_tuples(
            [
                ("Secured", "Mortgage"),
                ("Secured", "HELOC"),
                ("Unsecured", "Credit Card"),
                ("Unsecured", "Personal Loan"),
            ]
        )
        data = [
            ["€ 180.000,00", "€ 20.000,00", "€ 2.000,00", "€ 5.000,00"],
            ["€ 179.000,00", "€ 19.500,00", "€ 1.800,00", "€ 4.500,00"],
            ["€ 178.000,00", "€ 19.000,00", "€ 1.500,00", "€ 4.000,00"],
        ]
        df = pd.DataFrame(data, columns=columns)
        df.insert(0, ("Date", ""), ["2024-01", "2024-02", "2024-03"])
        return df

    def test_liabilities_single_index_structure(self, liabilities_single_index_data):
        """Test that single-index Liabilities DataFrame is correctly structured."""
        df = liabilities_single_index_data

        # Verify columns exist
        assert "Date" in df.columns
        assert "Mortgage" in df.columns
        assert "Car Loan" in df.columns

        # Verify data can be parsed
        assert parse_monetary_value(df["Mortgage"].iloc[0]) == pytest.approx(180000.0)
        assert parse_monetary_value(df["Car Loan"].iloc[1]) == pytest.approx(4500.0)

    def test_liabilities_multi_index_structure(self, liabilities_multi_index_data):
        """Test that multi-index Liabilities DataFrame is correctly structured."""
        df = liabilities_multi_index_data

        # Verify MultiIndex structure
        assert isinstance(df.columns, pd.MultiIndex)
        assert df.columns.nlevels == 2

        # Verify specific columns exist
        assert ("Secured", "Mortgage") in df.columns
        assert ("Unsecured", "Credit Card") in df.columns

        # Verify data can be parsed
        assert parse_monetary_value(df[("Secured", "Mortgage")].iloc[0]) == pytest.approx(180000.0)
        assert parse_monetary_value(df[("Unsecured", "Personal Loan")].iloc[2]) == pytest.approx(
            4000.0
        )

    def test_liabilities_single_index_with_calculator(self, liabilities_single_index_data):
        """Test FinanceCalculator with single-index Liabilities DataFrame."""
        main_df = pd.DataFrame(
            {
                "Date": ["2024-01", "2024-02", "2024-03"],
                "Net Worth": ["€ 30.000", "€ 31.000", "€ 32.000"],
                "Income": ["€ 3.000"] * 3,
                "Expenses": ["€ 2.000"] * 3,
            }
        )

        calc = FinanceCalculator(main_df, liabilities_df=liabilities_single_index_data)
        assets_liabilities = calc.get_assets_liabilities()

        # Verify Liabilities category exists
        assert "Liabilities" in assets_liabilities
        assert len(assets_liabilities["Liabilities"]) > 0

    def test_liabilities_multi_index_with_calculator(self, liabilities_multi_index_data):
        """Test FinanceCalculator with multi-index Liabilities DataFrame."""
        main_df = pd.DataFrame(
            {
                "Date": ["2024-01", "2024-02", "2024-03"],
                "Net Worth": ["€ 30.000", "€ 31.000", "€ 32.000"],
                "Income": ["€ 3.000"] * 3,
                "Expenses": ["€ 2.000"] * 3,
            }
        )

        calc = FinanceCalculator(main_df, liabilities_df=liabilities_multi_index_data)
        assets_liabilities = calc.get_assets_liabilities()

        # Verify Liabilities category exists
        assert "Liabilities" in assets_liabilities
        # With multi-index, we should have nested categories
        assert "Secured" in assets_liabilities["Liabilities"]
        assert "Unsecured" in assets_liabilities["Liabilities"]


class TestIncomesDataFrameStructure:
    """Tests for Incomes DataFrame with single and multi-index columns."""

    @pytest.fixture
    def incomes_single_index_data(self):
        """Create mock Incomes data with single-index columns (employee scenario)."""
        # Simulates Google Sheets structure:
        # Date    | Salary    | Side Hustle
        # 2024-01 | € 2.500   | € 200
        # 2024-02 | € 2.600   | € 300
        data = {
            "Date": ["2024-01", "2024-02", "2024-03"],
            "Salary": ["€ 2.500,00", "€ 2.600,00", "€ 2.700,00"],
            "Side Hustle": ["€ 200,00", "€ 300,00", "€ 400,00"],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def incomes_multi_index_data(self):
        """Create mock Incomes data with multi-index columns (freelance scenario)."""
        # Simulates Google Sheets structure:
        #             Regular         One-off
        # Date    | Salary | Rent   | Freelance | Bonus
        # 2024-01 | 2500   | 500    | 1000      | 0
        columns = pd.MultiIndex.from_tuples(
            [
                ("Regular", "Salary"),
                ("Regular", "Rent"),
                ("One-off", "Freelance"),
                ("One-off", "Bonus"),
            ]
        )
        data = [
            ["€ 2.500,00", "€ 500,00", "€ 1.000,00", "€ 0,00"],
            ["€ 2.600,00", "€ 500,00", "€ 1.200,00", "€ 500,00"],
            ["€ 2.700,00", "€ 500,00", "€ 800,00", "€ 0,00"],
        ]
        df = pd.DataFrame(data, columns=columns)
        df.insert(0, ("Date", ""), ["2024-01", "2024-02", "2024-03"])
        return df

    def test_incomes_single_index_structure(self, incomes_single_index_data):
        """Test that single-index Incomes DataFrame is correctly structured."""
        df = incomes_single_index_data

        # Verify columns exist
        assert "Date" in df.columns
        assert "Salary" in df.columns
        assert "Side Hustle" in df.columns

        # Verify data can be parsed
        assert parse_monetary_value(df["Salary"].iloc[0]) == pytest.approx(2500.0)
        assert parse_monetary_value(df["Side Hustle"].iloc[1]) == pytest.approx(300.0)
        # Verify total income can be calculated
        total_month_1 = parse_monetary_value(df["Salary"].iloc[0]) + parse_monetary_value(
            df["Side Hustle"].iloc[0]
        )
        assert total_month_1 == pytest.approx(2700.0)

    def test_incomes_multi_index_structure(self, incomes_multi_index_data):
        """Test that multi-index Incomes DataFrame is correctly structured."""
        df = incomes_multi_index_data

        # Verify MultiIndex structure
        assert isinstance(df.columns, pd.MultiIndex)
        assert df.columns.nlevels == 2

        # Verify specific columns exist
        assert ("Regular", "Salary") in df.columns
        assert ("One-off", "Freelance") in df.columns

        # Verify data can be parsed
        assert parse_monetary_value(df[("Regular", "Salary")].iloc[0]) == pytest.approx(2500.0)
        assert parse_monetary_value(df[("One-off", "Freelance")].iloc[1]) == pytest.approx(1200.0)
        # Verify total income can be calculated for a specific category
        regular_income_month_2 = parse_monetary_value(
            df[("Regular", "Salary")].iloc[1]
        ) + parse_monetary_value(df[("Regular", "Rent")].iloc[1])
        assert regular_income_month_2 == pytest.approx(3100.0)

    def test_incomes_single_index_total_calculation(self, incomes_single_index_data):
        """Test calculating total income from single-index Incomes DataFrame."""
        df = incomes_single_index_data

        # Calculate total income for all months
        for col in ["Salary", "Side Hustle"]:
            df[f"{col}_parsed"] = df[col].apply(parse_monetary_value)

        df["Total"] = df["Salary_parsed"] + df["Side Hustle_parsed"]

        assert df["Total"].iloc[0] == pytest.approx(2700.0)
        assert df["Total"].iloc[1] == pytest.approx(2900.0)
        assert df["Total"].iloc[2] == pytest.approx(3100.0)

    def test_incomes_multi_index_total_calculation(self, incomes_multi_index_data):
        """Test calculating total income from multi-index Incomes DataFrame."""
        df = incomes_multi_index_data

        # Calculate total income by summing all monetary columns
        total_income = []
        for idx in range(len(df)):
            row_total = 0
            for col in df.columns:
                if col != ("Date", ""):
                    row_total += parse_monetary_value(df[col].iloc[idx])
            total_income.append(row_total)

        assert total_income[0] == pytest.approx(4000.0)  # 2500 + 500 + 1000 + 0
        assert total_income[1] == pytest.approx(4800.0)  # 2600 + 500 + 1200 + 500
        assert total_income[2] == pytest.approx(4000.0)  # 2700 + 500 + 800 + 0
