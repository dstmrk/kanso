# app/logic/finance_calculator.py

import pandas as pd
from typing import Dict, Any, List, Optional
from functools import lru_cache

def parse_monetary_value(value: Any) -> float:
    """Utility function to parse monetary values from various formats."""
    if not isinstance(value, str):
        return float(value) if value is not None else 0.0
    try:
        cleaned_value = value.replace("€", "").replace(" ", "").replace(".", "").replace(",", ".")
        return float(cleaned_value)
    except (ValueError, TypeError):
        return 0.0

class FinanceCalculator:
    """Optimized finance calculator with cached DataFrame preprocessing."""
    
    def __init__(self, df: pd.DataFrame, expenses_df: Optional[pd.DataFrame] = None):
        self.original_df = df
        self.expenses_df = expenses_df
        self._processed_df = None
        self._processed_expenses_df = None
        
    @property 
    def processed_df(self) -> pd.DataFrame:
        """Lazily processed and cached main DataFrame."""
        if self._processed_df is None:
            self._processed_df = self._preprocess_main_df()
        return self._processed_df
        
    @property
    def processed_expenses_df(self) -> Optional[pd.DataFrame]:
        """Lazily processed and cached expenses DataFrame."""
        if self.expenses_df is not None and self._processed_expenses_df is None:
            self._processed_expenses_df = self._preprocess_expenses_df()
        return self._processed_expenses_df
    
    def _preprocess_main_df(self) -> pd.DataFrame:
        """Preprocess main DataFrame once with all required transformations."""
        df = self.original_df.copy()
        df['date_dt'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.sort_values(by='date_dt')
        
        # Parse monetary columns once
        monetary_columns = ['Net Worth', 'Income', 'Expenses', 'Cash', 'Pension Fund', 
                          'Stocks', 'Real Estate', 'Crypto', 'Other', 'Mortgage', 'Loans']
        for col in monetary_columns:
            if col in df.columns:
                df[f'{col.lower().replace(" ", "_")}_parsed'] = df[col].apply(parse_monetary_value)
        
        return df
        
    def _preprocess_expenses_df(self) -> pd.DataFrame:
        """Preprocess expenses DataFrame once."""
        if self.expenses_df is None:
            return None
            
        df = self.expenses_df.copy()
        df['date_dt'] = pd.to_datetime(df['Month'].astype(str).str.strip(), format='%Y-%m', errors='coerce')
        df['amount_parsed'] = df['Amount'].apply(parse_monetary_value)
        return df.sort_values(by='date_dt')
    
    def _validate_columns(self, required_columns: List[str]) -> bool:
        """Validate required columns exist."""
        missing_cols = [col for col in required_columns if col not in self.original_df.columns]
        if missing_cols:
            print(f"Error: DataFrame missing columns: {missing_cols}")
            return False
        return True
    
    def get_current_net_worth(self) -> float:
        """Get the most recent net worth value."""
        if not self._validate_columns(['Net Worth']):
            return 0.0
        return self.processed_df['net_worth_parsed'].iloc[-1]
    
    def get_last_update_date(self) -> str:
        """Get the date of the last update in MM-YYYY format."""
        return self.processed_df['date_dt'].iloc[-1].strftime('%m-%Y')
    
    def get_month_over_month_net_worth_variation_percentage(self) -> float:
        """Get month over month net worth percentage change."""
        if not self._validate_columns(['Net Worth']):
            return 0.0
        
        df = self.processed_df
        if len(df) < 2:
            return 0.0
            
        current = df['net_worth_parsed'].iloc[-1]
        previous = df['net_worth_parsed'].iloc[-2]
        
        return (current - previous) / previous if previous != 0 else 0.0
    
    def get_month_over_month_net_worth_variation_absolute(self) -> float:
        """Get month over month net worth absolute change."""
        if not self._validate_columns(['Net Worth']):
            return 0.0
        
        df = self.processed_df
        if len(df) < 2:
            return 0.0
            
        return df['net_worth_parsed'].iloc[-1] - df['net_worth_parsed'].iloc[-2]
    
    def get_year_over_year_net_worth_variation_percentage(self) -> float:
        """Get year over year net worth percentage change."""
        if not self._validate_columns(['Net Worth']):
            return 0.0
        
        df = self.processed_df
        if len(df) < 13:
            return 0.0
            
        current = df['net_worth_parsed'].iloc[-1]
        previous_year = df['net_worth_parsed'].iloc[-13]
        
        return (current - previous_year) / previous_year if previous_year != 0 else 0.0
    
    def get_year_over_year_net_worth_variation_absolute(self) -> float:
        """Get year over year net worth absolute change."""
        if not self._validate_columns(['Net Worth']):
            return 0.0
        
        df = self.processed_df
        if len(df) < 13:
            return 0.0
            
        return df['net_worth_parsed'].iloc[-1] - df['net_worth_parsed'].iloc[-13]
    
    def get_average_saving_ratio_last_12_months_percentage(self) -> float:
        """Get average saving ratio for last 12 months as percentage."""
        if not self._validate_columns(['Income', 'Expenses']):
            return 0.0
        
        df = self.processed_df
        income = df['income_parsed'].iloc[-12:].sum()
        expenses = df['expenses_parsed'].iloc[-12:].sum()
        
        return (income - expenses) / income if income != 0 else 0.0
    
    def get_average_saving_ratio_last_12_months_absolute(self) -> float:
        """Get average monthly savings for last 12 months."""
        if not self._validate_columns(['Income', 'Expenses']):
            return 0.0
        
        df = self.processed_df
        income = df['income_parsed'].iloc[-12:].sum()
        expenses = df['expenses_parsed'].iloc[-12:].sum()
        
        return (income - expenses) / 12 if income != 0 else 0.0
    
    def get_fi_progress(self) -> float:
        """Get FI progress - placeholder implementation."""
        return 0.263
    
    def get_monthly_net_worth(self) -> Dict[str, List]:
        """Get monthly net worth data for charting."""
        if not self._validate_columns(['Date', 'Net Worth']):
            return {'dates': [], 'values': []}
        
        df = self.processed_df.dropna(subset=['date_dt'])
        return {
            'dates': df['date_dt'].dt.strftime('%Y-%m').tolist(),
            'values': df['net_worth_parsed'].tolist()
        }
    
    def get_assets_liabilities(self) -> Dict[str, Dict[str, float]]:
        """Get latest assets and liabilities breakdown."""
        required_columns = ['Cash', 'Pension Fund', 'Stocks', 'Real Estate', 'Crypto', 'Other', 'Mortgage', 'Loans']
        if not self._validate_columns(required_columns):
            return {'Assets': {}, 'Liabilities': {}}
        
        latest = self.processed_df.iloc[-1]
        
        return {
            "Assets": {
                "Cash": latest['cash_parsed'],
                "Pension Fund": latest['pension_fund_parsed'],
                "Stocks": latest['stocks_parsed'],
                "Real Estate": latest['real_estate_parsed'],
                "Crypto": latest['crypto_parsed'],
                "Other": latest['other_parsed']
            },
            "Liabilities": {
                "Mortgage": latest['mortgage_parsed'],
                "Loans": latest['loans_parsed']
            }
        }
    
    def get_cash_flow_last_12_months(self) -> Dict[str, float]:
        """Get cash flow data for last 12 months."""
        if not self._validate_columns(['Income']):
            return {"Savings": 0.0, "Expenses": 0.0}
        
        if self.processed_expenses_df is None:
            return {"Savings": 0.0, "Expenses": 0.0}
        
        # Income from main df
        income = self.processed_df['income_parsed'].iloc[-12:].sum()
        
        # Expenses from expenses df (last 12 months)
        ef = self.processed_expenses_df
        latest_date = ef['date_dt'].max()
        start_date = (latest_date - pd.DateOffset(months=11)).replace(day=1)
        
        ef_last_12 = ef[(ef['date_dt'] >= start_date) & (ef['date_dt'] <= latest_date)]
        total_expenses = ef_last_12['amount_parsed'].sum()
        
        # Expenses by category
        expenses_by_category = ef_last_12.groupby('Category')['amount_parsed'].sum().to_dict()
        
        result = {"Expenses": total_expenses, "Savings": income - total_expenses}
        result.update(expenses_by_category)
        
        return result
    
    def get_average_expenses_by_category_last_12_months(self) -> Dict[str, float]:
        """Get average expenses by category for last 12 months."""
        if self.processed_expenses_df is None:
            return {}
        
        ef = self.processed_expenses_df
        latest_date = ef['date_dt'].max()
        start_date = (latest_date - pd.DateOffset(months=11)).replace(day=1)
        
        ef_last_12 = ef[(ef['date_dt'] >= start_date) & (ef['date_dt'] <= latest_date)]
        return ef_last_12.groupby('Category')['amount_parsed'].sum().to_dict()
    
    def get_incomes_vs_expenses(self) -> Dict[str, List]:
        """Get income vs expenses data for charting."""
        if not self._validate_columns(['Date', 'Income', 'Expenses']):
            return {'dates': [], 'incomes': [], 'expenses': []}
        
        df = self.processed_df.dropna(subset=['date_dt']).iloc[-12:]
        
        return {
            'dates': df['date_dt'].dt.strftime('%Y-%m').tolist(),
            'incomes': df['income_parsed'].tolist(),
            'expenses': [-x for x in df['expenses_parsed'].tolist()]  # Negative for chart
        }

# Backward compatibility functions (create FinanceCalculator internally for efficiency)
def get_current_net_worth(df: pd.DataFrame) -> float:
    return FinanceCalculator(df).get_current_net_worth()

def get_last_update_date(df: pd.DataFrame) -> str:
    return FinanceCalculator(df).get_last_update_date()

def get_month_over_month_net_worth_variation_percentage(df: pd.DataFrame) -> float:
    return FinanceCalculator(df).get_month_over_month_net_worth_variation_percentage()

def get_month_over_month_net_worth_variation_absolute(df: pd.DataFrame) -> float:
    return FinanceCalculator(df).get_month_over_month_net_worth_variation_absolute()

def get_year_over_year_net_worth_variation_percentage(df: pd.DataFrame) -> float:
    return FinanceCalculator(df).get_year_over_year_net_worth_variation_percentage()

def get_year_over_year_net_worth_variation_absolute(df: pd.DataFrame) -> float:
    return FinanceCalculator(df).get_year_over_year_net_worth_variation_absolute()

def get_average_saving_ratio_last_12_months_percentage(df: pd.DataFrame) -> float:
    return FinanceCalculator(df).get_average_saving_ratio_last_12_months_percentage()

def get_average_saving_ratio_last_12_months_absolute(df: pd.DataFrame) -> float:
    return FinanceCalculator(df).get_average_saving_ratio_last_12_months_absolute()

def get_fi_progress(df: pd.DataFrame) -> float:
    return FinanceCalculator(df).get_fi_progress()

def get_monthly_net_worth(df: pd.DataFrame) -> Dict[str, List]:
    return FinanceCalculator(df).get_monthly_net_worth()

def get_assets_liabilities(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    return FinanceCalculator(df).get_assets_liabilities()

def get_cash_flow_last_12_months(df: pd.DataFrame, ef: pd.DataFrame) -> Dict[str, float]:
    return FinanceCalculator(df, ef).get_cash_flow_last_12_months()

def get_average_expenses_by_category_last_12_months(ef: pd.DataFrame) -> Dict[str, float]:
    return FinanceCalculator(pd.DataFrame(), ef).get_average_expenses_by_category_last_12_months()

def get_incomes_vs_expenses(df: pd.DataFrame) -> Dict[str, List]:
    return FinanceCalculator(df).get_incomes_vs_expenses()