"""
Centralized constants for the Kanso application.

This module contains all hardcoded strings, numbers, and configuration values
used throughout the application to improve maintainability and consistency.
"""

# === DataFrame Column Names ===

# Main data sheet columns
COL_DATE = "Date"
COL_NET_WORTH = "Net Worth"
COL_INCOME = "Income"
COL_EXPENSES = "Expenses"
COL_CASH = "Cash"
COL_PENSION_FUND = "Pension Fund"
COL_STOCKS = "Stocks"
COL_REAL_ESTATE = "Real Estate"
COL_CRYPTO = "Crypto"
COL_OTHER = "Other"
COL_MORTGAGE = "Mortgage"
COL_LOANS = "Loans"

# Expenses sheet columns
COL_MONTH = "Month"
COL_AMOUNT = "Amount"
COL_CATEGORY = "Category"

# Computed/internal columns
COL_DATE_DT = "date_dt"
COL_NET_WORTH_PARSED = "net_worth_parsed"
COL_INCOME_PARSED = "income_parsed"
COL_EXPENSES_PARSED = "expenses_parsed"
COL_AMOUNT_PARSED = "amount_parsed"

# All monetary columns for main data sheet
MONETARY_COLUMNS = [
    COL_NET_WORTH,
    COL_INCOME,
    COL_EXPENSES,
    COL_CASH,
    COL_PENSION_FUND,
    COL_STOCKS,
    COL_REAL_ESTATE,
    COL_CRYPTO,
    COL_OTHER,
    COL_MORTGAGE,
    COL_LOANS,
]

# === Category Names ===

CATEGORY_ASSETS = "Assets"
CATEGORY_LIABILITIES = "Liabilities"
CATEGORY_SAVINGS = "Savings"
CATEGORY_EXPENSES = "Expenses"

# === Date Formats ===

# Standard date format for storage (YYYY-MM)
DATE_FORMAT_STORAGE = "%Y-%m"

# Display date format (MM-YYYY)
DATE_FORMAT_DISPLAY = "%m-%Y"

# === Cache Settings ===

# Default cache TTL in seconds (24 hours)
# Suitable for monthly financial data updates
CACHE_TTL_SECONDS = 86400

# === Google Sheets Worksheet Names ===
# Note: These are also defined in config.py with env variable fallbacks
# These serve as default constants

SHEET_NAME_DATA = "Data"
SHEET_NAME_ASSETS = "Assets"
SHEET_NAME_LIABILITIES = "Liabilities"
SHEET_NAME_EXPENSES = "Expenses"

# === Time Periods ===

# Number of months for various calculations
MONTHS_IN_YEAR = 12
MONTHS_LOOKBACK_YEAR = 13  # 12 months + 1 for YoY comparison
