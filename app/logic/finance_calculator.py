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
    # Check for required columns to avoid errors
    required_columns = ["Date", "Net Worth"]
    if not all(col in df.columns for col in required_columns):
        print(f"Error: DataFrame is missing one of the required columns: {required_columns}")
        return {'dates': [], 'values': []} # Return empty structure

    # Create a copy to avoid modifying the original DataFrame (good practice)
    df_copy = df.copy()

    # --- Data Cleaning and Processing ---
    # 1. Apply the parsing function to the 'Net Worth' column
    df_copy['net_worth_clean'] = df_copy['Net Worth'].apply(parse_monetary_value)
    
    # 2. Convert 'Date' column to datetime objects for proper sorting
    #    'errors='coerce'' will turn unparseable dates into NaT (Not a Time)
    df_copy['date_dt'] = pd.to_datetime(df_copy['Date'], errors='coerce')
    
    # 3. Drop rows where the date could not be parsed
    df_copy.dropna(subset=['date_dt'], inplace=True)

    # 4. Sort the DataFrame by date to ensure the chart is chronological
    df_sorted = df_copy.sort_values(by='date_dt')

    # --- Formatting for ECharts ---
    # 5. Format the dates into 'YYYY-MM' strings for the x-axis labels
    dates_for_chart = df_sorted['date_dt'].dt.strftime('%Y-%m').tolist()
    
    # 6. Get the clean numeric values for the y-axis
    values_for_chart = df_sorted['net_worth_clean'].tolist()

    return {
        'dates': dates_for_chart,
        'values': values_for_chart
    }