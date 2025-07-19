# app/logic/finance_calculator.py

import pandas as pd
from typing import Dict, Any, List

def parse_monetary_value(value: Any) -> float:
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
    
def get_current_net_worth(df: pd.DataFrame) -> float:
    latest_net_worth = 0.0
    required_columns = ["Net Worth"]
    if not all(col in df.columns for col in required_columns):
        print(f"Error: DataFrame is missing one of the required columns: {required_columns}")
    else:
        df_copy = df.copy()
        df_copy['date_dt'] = pd.to_datetime(df_copy['Date'], errors='coerce')
        df_sorted = df_copy.sort_values(by='date_dt')
        latest_net_worth = parse_monetary_value(df_sorted["Net Worth"].iloc[-1])
    return latest_net_worth
    

def get_month_over_month_net_worth_variation(df: pd.DataFrame) -> float:
    mom_variation = 0.0
    required_columns = ["Net Worth"]
    if not all(col in df.columns for col in required_columns):
        print(f"Error: DataFrame is missing one of the required columns: {required_columns}")
    else:
        df_copy = df.copy()
        df_copy['date_dt'] = pd.to_datetime(df_copy['Date'], errors='coerce')
        df_sorted = df_copy.sort_values(by='date_dt')
        previous_month_net_worth = parse_monetary_value(df_sorted["Net Worth"].iloc[-2])
        current_net_worth = get_current_net_worth(df)
        if previous_month_net_worth != 0:
            mom_variation = (current_net_worth - previous_month_net_worth)/previous_month_net_worth
    return mom_variation

def get_average_saving_ratio_last_12_months(df: pd.DataFrame) -> float:
    avg_saving_ratio = 0.0
    required_columns = ["Income", "Expenses"]
    if not all(col in df.columns for col in required_columns):
        print(f"Error: DataFrame is missing one of the required columns: {required_columns}")
    else:
        df_copy = df.copy()
        df_copy['date_dt'] = pd.to_datetime(df_copy['Date'], errors='coerce')
        df_sorted = df_copy.sort_values(by='date_dt')
        income = df_sorted["Income"].iloc[-12:].apply(parse_monetary_value).sum()
        expenses = df_sorted["Expenses"].iloc[-12:].apply(parse_monetary_value).sum()
        if income != 0:
            avg_saving_ratio = (income - expenses)/income
    return avg_saving_ratio

def get_fi_progress(df: pd.DataFrame) -> float:
    return 0.263

def get_monthly_net_worth(df: pd.DataFrame) -> Dict[str, List]:
    monthly_net_worth = {'dates': [], 'values': []}
    required_columns = ["Date", "Net Worth"]
    if not all(col in df.columns for col in required_columns):
        print(f"Error: DataFrame is missing one of the required columns: {required_columns}")
    else:
        df_copy = df.copy()
        df_copy['date_dt'] = pd.to_datetime(df_copy['Date'], errors='coerce')
        df_copy['net_worth_clean'] = df_copy['Net Worth'].apply(parse_monetary_value)
        df_copy.dropna(subset=['date_dt'], inplace=True)
        df_sorted = df_copy.sort_values(by='date_dt')
        dates_for_chart = df_sorted['date_dt'].dt.strftime('%Y-%m').tolist()
        values_for_chart = df_sorted['net_worth_clean'].tolist()
        monthly_net_worth = {
            'dates': dates_for_chart,
            'values': values_for_chart
            }
    return monthly_net_worth
    
def get_assets_liabilities(df: pd.DataFrame) -> Dict[str, List]:
    asset_liabilities = {'Assets': {}, 'Liabilities': {}}
    required_columns = ["Date", "Cash", "Pension Fund", "Stocks", "Real Estate", "Crypto", "Other", "Mortgage", "Loans"]
    if not all(col in df.columns for col in required_columns):
        print(f"Error: DataFrame is missing one of the required columns: {required_columns}")
    else:
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
        asset_liabilities = {
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
    return asset_liabilities