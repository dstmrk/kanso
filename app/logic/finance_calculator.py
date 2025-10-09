# app/logic/finance_calculator.py

import logging
import pandas as pd
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

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

    def __init__(self, df: pd.DataFrame, assets_df: Optional[pd.DataFrame] = None, liabilities_df: Optional[pd.DataFrame] = None, expenses_df: Optional[pd.DataFrame] = None) -> None:
        self.original_df = df
        self.expenses_df = expenses_df
        self.assets_df = assets_df
        self.liabilities_df = liabilities_df
        self._processed_df = None
        self._processed_expenses_df = None
        self._processed_assets_df = None
        self._processed_liabilities_df = None
        
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

    @property
    def processed_assets_df(self) -> Optional[pd.DataFrame]:
        """Lazily processed and cached assets DataFrame."""
        if self.assets_df is not None and self._processed_assets_df is None:
            self._processed_assets_df = self._preprocess_assets_df()
        return self._processed_assets_df

    @property
    def processed_liabilities_df(self) -> Optional[pd.DataFrame]:
        """Lazily processed and cached liabilities DataFrame."""
        if self.liabilities_df is not None and self._processed_liabilities_df is None:
            self._processed_liabilities_df = self._preprocess_liabilities_df()
        return self._processed_liabilities_df

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
        
    def _preprocess_expenses_df(self) -> Optional[pd.DataFrame]:
        """Preprocess expenses DataFrame once."""
        if self.expenses_df is None:
            return None

        df = self.expenses_df.copy()
        df['date_dt'] = pd.to_datetime(df['Month'].astype(str).str.strip(), format='%Y-%m', errors='coerce')
        df['amount_parsed'] = df['Amount'].apply(parse_monetary_value)
        return df.sort_values(by='date_dt')

    def _preprocess_assets_df(self) -> Optional[pd.DataFrame]:
        """Preprocess assets DataFrame once with date parsing and sorting."""
        if self.assets_df is None or self.assets_df.empty:
            return None

        df = self.assets_df.copy()

        # Find Date column (handles MultiIndex)
        date_col = None
        for col in df.columns:
            if isinstance(col, tuple):
                if 'Date' in col[0] or 'Date' in col[1]:
                    date_col = col
                    break
            else:
                if 'Date' in col:
                    date_col = col
                    break

        if date_col is not None:
            df['date_dt'] = pd.to_datetime(df[date_col], format='%Y-%m', errors='coerce')
            df = df.sort_values(by='date_dt')

        return df

    def _preprocess_liabilities_df(self) -> Optional[pd.DataFrame]:
        """Preprocess liabilities DataFrame once with date parsing and sorting."""
        if self.liabilities_df is None or self.liabilities_df.empty:
            return None

        df = self.liabilities_df.copy()

        # Find Date column (handles MultiIndex)
        date_col = None
        for col in df.columns:
            if isinstance(col, tuple):
                if any(keyword in col[0] or keyword in col[1] for keyword in ['Date', 'Data', 'Category']):
                    date_col = col
                    break
            else:
                if any(keyword in col for keyword in ['Date', 'Data', 'Category']):
                    date_col = col
                    break

        if date_col is not None:
            df['date_dt'] = pd.to_datetime(df[date_col], format='%Y-%m', errors='coerce')
            df = df.sort_values(by='date_dt')

        return df

    def _validate_columns(self, required_columns: List[str]) -> bool:
        """Validate required columns exist."""
        missing_cols = [col for col in required_columns if col not in self.original_df.columns]
        if missing_cols:
            logger.error(f"DataFrame missing required columns: {missing_cols}")
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
            
        current: float = df['net_worth_parsed'].iloc[-1]
        previous: float = df['net_worth_parsed'].iloc[-2]
        
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
            
        current: float = df['net_worth_parsed'].iloc[-1]
        previous_year: float = df['net_worth_parsed'].iloc[-13]
        
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
        income: float = df['income_parsed'].iloc[-12:].sum()
        expenses: float = df['expenses_parsed'].iloc[-12:].sum()

        return (income - expenses) / income if income != 0 else 0.0

    def get_average_saving_ratio_last_12_months_absolute(self) -> float:
        """Get average monthly savings for last 12 months."""
        if not self._validate_columns(['Income', 'Expenses']):
            return 0.0

        df = self.processed_df
        income: float = df['income_parsed'].iloc[-12:].sum()
        expenses: float = df['expenses_parsed'].iloc[-12:].sum()

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
    def get_assets_liabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get assets and liabilities breakdown from the latest data."""
        asset_liabilities: Dict[str, Dict[str, Any]] = {'Assets': {}, 'Liabilities': {}}
        reference_date = None

        # Use preprocessed DataFrames
        assets_df = self.processed_assets_df
        liabilities_df = self.processed_liabilities_df

        if assets_df is not None and not assets_df.empty:
            # Get latest row
            latest_row = assets_df.iloc[-1]
            reference_date = assets_df['date_dt'].iloc[-1]

            # Extract values dynamically from columns
            for col in assets_df.columns:
                # Skip date_dt column
                if col == 'date_dt':
                    continue
                # Skip if column name contains 'date_dt' (handles both tuple and string columns)
                if (isinstance(col, tuple) and 'date_dt' in col):
                    continue
                # Skip Date column
                if isinstance(col, tuple):
                    if 'Date' in col[0] or 'Date' in col[1]:
                        continue
                else:
                    if 'Date' in col:
                        continue

                if isinstance(col, tuple) and len(col) == 2:
                    # MultiIndex: (category, item)
                    category, item = col
                    category = category.strip()
                    item = item.strip()
                    if not category:
                        continue
                    value = parse_monetary_value(latest_row[col])
                    if category not in asset_liabilities['Assets']:
                        asset_liabilities['Assets'][category] = {}
                    asset_liabilities['Assets'][category][item] = value
                else:
                    # Single header: column name is the item
                    item = col
                    value = parse_monetary_value(latest_row[col])
                    asset_liabilities['Assets'][item] = value

        # Process Liabilities DataFrame
        if liabilities_df is not None and not liabilities_df.empty:
            # Use reference date from Assets to get the corresponding row
            if reference_date is not None:
                matching_rows = liabilities_df[liabilities_df['date_dt'] <= reference_date]
                if not matching_rows.empty:
                    latest_row = matching_rows.iloc[-1]
                else:
                    latest_row = liabilities_df.iloc[-1]
            else:
                latest_row = liabilities_df.iloc[-1]

            # Extract values dynamically from columns
            for col in liabilities_df.columns:
                # Skip date_dt column
                if col == 'date_dt':
                    continue
                # Skip if column name contains 'date_dt' (handles both tuple and string columns)
                if (isinstance(col, tuple) and 'date_dt' in col):
                    continue
                # Skip Date column
                if isinstance(col, tuple):
                    if any(keyword in col[0] or keyword in col[1] for keyword in ['Date', 'Data', 'Category']):
                        continue
                else:
                    if any(keyword in col for keyword in ['Date', 'Data', 'Category']):
                        continue

                if isinstance(col, tuple) and len(col) == 2:
                    # MultiIndex: (category, item)
                    category, item = col
                    category = category.strip()
                    item = item.strip()
                    if not category or category == 'Category':
                        continue
                    value = parse_monetary_value(latest_row[col])
                    if category not in asset_liabilities['Liabilities']:
                        asset_liabilities['Liabilities'][category] = {}
                    asset_liabilities['Liabilities'][category][item] = value
                else:
                    # Single header: column name is the item
                    item = col
                    value = parse_monetary_value(latest_row[col])
                    asset_liabilities['Liabilities'][item] = value

        return asset_liabilities
    
    def get_cash_flow_last_12_months(self) -> Dict[str, float]:
        """Get cash flow data for last 12 months."""
        if not self._validate_columns(['Income']):
            return {"Savings": 0.0, "Expenses": 0.0}
        
        if self.processed_expenses_df is None:
            return {"Savings": 0.0, "Expenses": 0.0}
        
        # Income from main df
        income = self.processed_df['income_parsed'].iloc[-12:].sum()
        
        # Expenses from expenses df (last 12 months)
        ef: pd.DataFrame = self.processed_expenses_df
        latest_date: pd.Timestamp = ef['date_dt'].max()
        start_date: pd.Timestamp = (latest_date - pd.DateOffset(months=11)).replace(day=1)
        
        ef_last_12: pd.DataFrame = ef[(ef['date_dt'] >= start_date) & (ef['date_dt'] <= latest_date)]
        total_expenses: float = ef_last_12['amount_parsed'].sum()
        
        # Expenses by category
        expenses_by_category: Dict[str, float] = ef_last_12.groupby('Category')['amount_parsed'].sum().to_dict()
        
        result: Dict[str, float] = {"Expenses": total_expenses, "Savings": income - total_expenses}
        result.update(expenses_by_category)
        
        return result
    
    def get_average_expenses_by_category_last_12_months(self) -> Dict[str, float]:
        """Get average expenses by category for last 12 months."""
        if self.processed_expenses_df is None:
            return {}
        
        ef: pd.DataFrame = self.processed_expenses_df
        latest_date: pd.Timestamp = ef['date_dt'].max()
        start_date: pd.Timestamp = (latest_date - pd.DateOffset(months=11)).replace(day=1)
        
        ef_last_12: pd.DataFrame = ef[(ef['date_dt'] >= start_date) & (ef['date_dt'] <= latest_date)]
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

