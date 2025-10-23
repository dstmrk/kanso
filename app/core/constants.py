"""Centralized constants for the Kanso application.

This module contains all hardcoded strings, numbers, and configuration values
used throughout the application to improve maintainability and consistency.
"""

# === DataFrame Column Names ===

# Common columns across sheets
COL_DATE = "Date"

# Expenses sheet columns
COL_MERCHANT = "Merchant"
COL_AMOUNT = "Amount"
COL_CATEGORY = "Category"
COL_TYPE = "Type"

# Computed/internal columns (created during preprocessing)
COL_DATE_DT = "date_dt"
COL_NET_WORTH_PARSED = "net_worth_parsed"
COL_AMOUNT_PARSED = "amount_parsed"

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

SHEET_NAME_ASSETS = "Assets"
SHEET_NAME_LIABILITIES = "Liabilities"
SHEET_NAME_EXPENSES = "Expenses"
SHEET_NAME_INCOMES = "Incomes"

# === Time Periods ===

# Number of months for various calculations
MONTHS_IN_YEAR = 12
MONTHS_LOOKBACK_YEAR = 13  # 12 months + 1 for YoY comparison
