"""Test cash flow Sankey diagram with multiple income sources.

Tests that the cash flow visualization correctly handles both single and multiple
income sources, creating appropriate Sankey diagram structures.
"""

import pandas as pd
import pytest

from app.logic.finance_calculator import FinanceCalculator
from app.ui.charts import create_cash_flow_options


def test_cash_flow_with_single_income_source():
    """Test cash flow with single income source."""
    # Single income source
    incomes_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02", "2024-03"] * 4,  # 12 months
            "Salary": ["€ 3.000"] * 12,
        }
    )

    # Expenses
    expenses_df = pd.DataFrame(
        {
            "Date": ["2024-01"] * 3 + ["2024-02"] * 3 + ["2024-03"] * 3,
            "Merchant": ["Store"] * 9,
            "Amount": ["€ 500"] * 6 + ["€ 1.000"] * 3,  # Mix of amounts
            "Category": ["Food", "Transport", "Housing"] * 3,
            "Type": ["Variable"] * 9,
        }
    )

    calculator = FinanceCalculator(expenses_df=expenses_df, incomes_df=incomes_df)
    cash_flow = calculator.get_cash_flow_last_12_months()

    # Should have single income source
    assert "Salary" in cash_flow
    assert "Savings" in cash_flow
    assert "Expenses" in cash_flow

    # Chart should have single income node (no aggregation)
    chart_options = create_cash_flow_options(cash_flow, "desktop", "EUR")
    nodes = chart_options["series"][0]["data"]
    node_names = [node["name"] for node in nodes]

    assert "Salary" in node_names
    assert "Total Income" not in node_names  # Single source, no aggregation node


def test_cash_flow_with_multiple_income_sources():
    """Test cash flow with multiple income sources."""
    # Multiple income sources with MultiIndex
    incomes_df = pd.DataFrame(
        {
            ("Date", ""): ["2024-01", "2024-02", "2024-03"] * 4,
            ("Salary", "Company"): ["€ 3.000"] * 12,
            ("Freelance", "Projects"): ["€ 1.000"] * 12,
            ("Investments", "Dividends"): ["€ 500"] * 12,
        }
    )
    # Convert to MultiIndex
    incomes_df.columns = pd.MultiIndex.from_tuples(incomes_df.columns)

    # Expenses
    expenses_df = pd.DataFrame(
        {
            "Date": ["2024-01"] * 3 + ["2024-02"] * 3 + ["2024-03"] * 3,
            "Merchant": ["Store"] * 9,
            "Amount": ["€ 500"] * 6 + ["€ 1.000"] * 3,
            "Category": ["Food", "Transport", "Housing"] * 3,
            "Type": ["Variable"] * 9,
        }
    )

    calculator = FinanceCalculator(expenses_df=expenses_df, incomes_df=incomes_df)
    cash_flow = calculator.get_cash_flow_last_12_months()

    # Should have separate income sources
    # With MultiIndex ("Salary", "Company"), we take the LAST (most specific) → "Company"
    assert "Company" in cash_flow  # From ("Salary", "Company")
    assert "Projects" in cash_flow  # From ("Freelance", "Projects")
    assert "Dividends" in cash_flow  # From ("Investments", "Dividends")
    assert "Savings" in cash_flow
    assert "Expenses" in cash_flow

    # Chart should have multiple income nodes + aggregation node
    chart_options = create_cash_flow_options(cash_flow, "desktop", "EUR")
    nodes = chart_options["series"][0]["data"]
    links = chart_options["series"][0]["links"]

    node_names = [node["name"] for node in nodes]

    # Check nodes - using most specific names from MultiIndex
    # ("Salary", "Company") → "Company", ("Freelance", "Projects") → "Projects", etc.
    assert "Company" in node_names
    assert "Projects" in node_names
    assert "Dividends" in node_names
    assert "Total Income" in node_names  # Aggregation node should exist
    assert "Savings" in node_names
    assert "Expenses" in node_names

    # Check links structure: Sources → Total Income → Savings/Expenses
    # Income sources should flow to Total Income
    target_names = [link["target"] for link in links]
    assert "Total Income" in target_names
    assert any(link["source"] == "Company" and link["target"] == "Total Income" for link in links)
    assert any(link["source"] == "Projects" and link["target"] == "Total Income" for link in links)
    assert any(link["source"] == "Dividends" and link["target"] == "Total Income" for link in links)

    # Total Income should flow to Savings and Expenses
    assert any(link["source"] == "Total Income" and link["target"] == "Savings" for link in links)
    assert any(link["source"] == "Total Income" and link["target"] == "Expenses" for link in links)


def test_income_sources_breakdown():
    """Test that income sources are correctly extracted and totaled."""
    # Income sources
    incomes_df = pd.DataFrame(
        {
            ("Date", ""): ["2024-01", "2024-02"],
            ("Salary", "Company"): ["€ 3.000", "€ 3.000"],
            ("Freelance", "Projects"): ["€ 1.000", "€ 1.200"],
        }
    )
    incomes_df.columns = pd.MultiIndex.from_tuples(incomes_df.columns)

    expenses_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02"],
            "Merchant": ["Store", "Store"],
            "Amount": ["€ 1.500", "€ 1.500"],
            "Category": ["Food", "Food"],
            "Type": ["Variable", "Variable"],
        }
    )

    calculator = FinanceCalculator(expenses_df=expenses_df, incomes_df=incomes_df)
    cash_flow = calculator.get_cash_flow_last_12_months()

    # Check individual sources - using most specific names from MultiIndex
    # ("Salary", "Company") → "Company", ("Freelance", "Projects") → "Projects"
    assert cash_flow["Company"] == pytest.approx(6000.0, rel=0.01)  # 3000*2
    assert cash_flow["Projects"] == pytest.approx(2200.0, rel=0.01)  # 1000+1200

    # Check total calculations
    total_income = cash_flow["Company"] + cash_flow["Projects"]
    total_expenses = cash_flow["Expenses"]
    expected_savings = total_income - total_expenses

    assert cash_flow["Savings"] == pytest.approx(expected_savings, rel=0.01)


def test_multiple_sources_with_single_index():
    """Test multiple income sources with SINGLE-INDEX columns (not MultiIndex).

    This is the typical case where user has:
    Date | Salary | Freelance | Investments
    """
    # Single-index with multiple income columns
    incomes_df = pd.DataFrame(
        {
            "Date": ["2024-01", "2024-02", "2024-03"] * 4,
            "Salary": ["€ 3.000"] * 12,
            "Freelance": ["€ 1.000"] * 12,
            "Investments": ["€ 500"] * 12,
        }
    )

    # Expenses
    expenses_df = pd.DataFrame(
        {
            "Date": ["2024-01"] * 3 + ["2024-02"] * 3 + ["2024-03"] * 3,
            "Merchant": ["Store"] * 9,
            "Amount": ["€ 800"] * 9,
            "Category": ["Food", "Transport", "Housing"] * 3,
            "Type": ["Variable"] * 9,
        }
    )

    calculator = FinanceCalculator(expenses_df=expenses_df, incomes_df=incomes_df)
    cash_flow = calculator.get_cash_flow_last_12_months()

    # Should have separate income sources (NOT aggregated as "Income")
    assert "Salary" in cash_flow
    assert "Freelance" in cash_flow
    assert "Investments" in cash_flow

    # Verify amounts
    assert cash_flow["Salary"] == pytest.approx(36000.0, rel=0.01)  # 3000*12
    assert cash_flow["Freelance"] == pytest.approx(12000.0, rel=0.01)  # 1000*12
    assert cash_flow["Investments"] == pytest.approx(6000.0, rel=0.01)  # 500*12

    # Chart should show multiple sources
    chart_options = create_cash_flow_options(cash_flow, "desktop", "EUR")
    nodes = chart_options["series"][0]["data"]
    node_names = [node["name"] for node in nodes]

    assert "Salary" in node_names
    assert "Freelance" in node_names
    assert "Investments" in node_names
    assert "Total Income" in node_names  # Should have aggregation node


def test_chart_structure_with_two_sources():
    """Test Sankey structure is correct with exactly 2 sources."""
    cash_flow_data = {
        "Salary": 30000.0,
        "Freelance": 5000.0,
        "Expenses": 20000.0,
        "Savings": 15000.0,
        "Food": 8000.0,
        "Transport": 6000.0,
        "Housing": 6000.0,
    }

    chart = create_cash_flow_options(cash_flow_data, "desktop", "EUR")
    nodes = chart["series"][0]["data"]
    links = chart["series"][0]["links"]

    # Verify node count: 2 sources + Total Income + Savings + Expenses + 3 categories = 8
    assert len(nodes) == 8

    # Verify link count: 2 (sources→total) + 2 (total→savings/expenses) + 3 (expenses→cats) = 7
    assert len(links) == 7

    # Verify amounts
    salary_link = next(
        link for link in links if link["source"] == "Salary" and link["target"] == "Total Income"
    )
    assert salary_link["value"] == pytest.approx(30000.0)
    freelance_link = next(
        link for link in links if link["source"] == "Freelance" and link["target"] == "Total Income"
    )
    assert freelance_link["value"] == pytest.approx(5000.0)
