# app/logic/finance_calculator.py

import pandas as pd
from typing import Dict, Any, List

def parse_monetary_value(value: Any) -> float:
    """
    Cleans a European-style monetary string and converts it to a float.
    Handles '€', spaces, thousand separators ('.') and decimal commas (',').
    
    Example: "€ 1.234,56" -> 1234.56
    
    Returns 0.0 if the input is empty or cannot be converted.
    """
    if not isinstance(value, str):
        # If it's already a number (int, float) or None, return it as a float
        return float(value) if value is not None else 0.0
    
    try:
        # Chain of replacements to handle the European format
        cleaned_value = value.replace("€", "").replace(" ", "").replace(".", "").replace(",", ".")
        return float(cleaned_value)
    except (ValueError, TypeError):
        # If conversion fails for any reason, return a safe default
        return 0.0


def get_monthly_net_worth(df: pd.DataFrame) -> Dict[str, List]:
    """
    Processes a DataFrame to extract monthly net worth data for ECharts.
    
    Args:
        df: DataFrame from Google Sheets with 'Date' and 'Net Worth' columns.

    Returns:
        A dictionary formatted for ECharts with two keys:
        - 'dates': A list of formatted date strings (e.g., '2023-12').
        - 'values': A list of net worth floats.
    """
    required_columns = ["Date", "Net Worth"]
    if not all(col in df.columns for col in required_columns):
        print(f"Error: DataFrame is missing one of the required columns: {required_columns}")
        return {'dates': [], 'values': []}
    df_copy = df.copy()
    df_copy['date_dt'] = pd.to_datetime(df_copy['Date'], errors='coerce')
    df_copy['net_worth_clean'] = df_copy['Net Worth'].apply(parse_monetary_value)
    df_copy.dropna(subset=['date_dt'], inplace=True)
    df_sorted = df_copy.sort_values(by='date_dt')
    dates_for_chart = df_sorted['date_dt'].dt.strftime('%Y-%m').tolist()
    values_for_chart = df_sorted['net_worth_clean'].tolist()
    return {
        'dates': dates_for_chart,
        'values': values_for_chart
    }
    
def get_assets_liabilities(df: pd.DataFrame) -> Dict[str, List]:
    """
    Processes a DataFrame to extract monthly net worth data for ECharts.
    
    Args:
        df: DataFrame from Google Sheets with 'Date' and 'Net Worth' columns.

    Returns:
        A dictionary formatted for ECharts with two keys:
        - 'dates': A list of formatted date strings (e.g., '2023-12').
        - 'values': A list of net worth floats.
    """
    # Check for required columns to avoid errors
    required_columns = ["Date", "Cash", "Pension Fund", "Stocks", "Real Estate", "Crypto", "Other", "Mortgage", "Loans"]
    if not all(col in df.columns for col in required_columns):
        print(f"Error: DataFrame is missing one of the required columns: {required_columns}")
        return {'Assets': {}, 'Liabilities': {}}
    df_copy = df.copy()
    df_copy['date_dt'] = pd.to_datetime(df_copy['Date'], errors='coerce')
    df_sorted = df_copy.sort_values(by='date_dt')
    latest_row = df_sorted.iloc[-1]
    latest_cash = parse_monetary_value(latest_row["Cash"])
    latest_pension_fund = parse_monetary_value(latest_row["Pension Fund"])
    latest_stocks = parse_monetary_value(latest_row["Stocks"])
    latest_real_estate = parse_monetary_value(latest_row["Real Estate"])
    latest_crypto = parse_monetary_value(latest_row["Crypto"])
    latest_other = parse_monetary_value(latest_row["Other"])
    latest_mortgage = parse_monetary_value(latest_row["Mortgage"])
    latest_loans = parse_monetary_value(latest_row["Loans"])
    return {
        "Assets": {
            "Cash": latest_cash,
            "Pension Fund": latest_pension_fund,
            "Stocks": latest_stocks,
            "Real Estate": latest_real_estate,
            "Crypto": latest_crypto,
            "Other": latest_other
        },
        "Liabilities": {
            "Mortgage": latest_mortgage,
            "Loans": latest_loans
        }
    }