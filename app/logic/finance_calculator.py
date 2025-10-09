# app/logic/finance_calculator.py

import logging
import pandas as pd
from typing import Dict, Any, List, Optional

from app.core.constants import (
    COL_DATE, COL_NET_WORTH, COL_INCOME, COL_EXPENSES,
    COL_MONTH, COL_AMOUNT, COL_CATEGORY,
    COL_DATE_DT, COL_NET_WORTH_PARSED, COL_INCOME_PARSED,
    COL_EXPENSES_PARSED, COL_AMOUNT_PARSED,
    MONETARY_COLUMNS, CATEGORY_ASSETS, CATEGORY_LIABILITIES,
    CATEGORY_SAVINGS, CATEGORY_EXPENSES,
    DATE_FORMAT_STORAGE, DATE_FORMAT_DISPLAY,
    MONTHS_IN_YEAR, MONTHS_LOOKBACK_YEAR
)

logger = logging.getLogger(__name__)

def parse_monetary_value(value: Any) -> float:
    """Utility function to parse monetary values from various formats."""
    if not isinstance(value, str):
        return float(value) if value is not None else 0.0
    try:
        cleaned_value = value.replace("€", "").replace('$', '').replace('£', '').replace('Fr', '').replace('¥', '').replace(" ", "").replace(".", "").replace(",", ".")
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
        df[COL_DATE_DT] = pd.to_datetime(df[COL_DATE], errors='coerce')
        df = df.sort_values(by=COL_DATE_DT)

        # Parse monetary columns once
        for col in MONETARY_COLUMNS:
            if col in df.columns:
                df[f'{col.lower().replace(" ", "_")}_parsed'] = df[col].apply(parse_monetary_value)

        return df
        
    def _preprocess_expenses_df(self) -> Optional[pd.DataFrame]:
        """Preprocess expenses DataFrame once."""
        if self.expenses_df is None:
            return None

        df = self.expenses_df.copy()
        df[COL_DATE_DT] = pd.to_datetime(df[COL_MONTH].astype(str).str.strip(), format=DATE_FORMAT_STORAGE, errors='coerce')
        df[COL_AMOUNT_PARSED] = df[COL_AMOUNT].apply(parse_monetary_value)
        return df.sort_values(by=COL_DATE_DT)

    def _preprocess_assets_df(self) -> Optional[pd.DataFrame]:
        """Preprocess assets DataFrame once with date parsing and sorting."""
        if self.assets_df is None or self.assets_df.empty:
            return None

        df = self.assets_df.copy()

        # Find Date column (handles MultiIndex)
        date_col = None
        for col in df.columns:
            if isinstance(col, tuple):
                if COL_DATE in col[0] or COL_DATE in col[1]:
                    date_col = col
                    break
            else:
                if COL_DATE in col:
                    date_col = col
                    break

        if date_col is not None:
            df[COL_DATE_DT] = pd.to_datetime(df[date_col], format=DATE_FORMAT_STORAGE, errors='coerce')
            df = df.sort_values(by=COL_DATE_DT)

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
                if any(keyword in col[0] or keyword in col[1] for keyword in [COL_DATE, 'Data', COL_CATEGORY]):
                    date_col = col
                    break
            else:
                if any(keyword in col for keyword in [COL_DATE, 'Data', COL_CATEGORY]):
                    date_col = col
                    break

        if date_col is not None:
            df[COL_DATE_DT] = pd.to_datetime(df[date_col], format=DATE_FORMAT_STORAGE, errors='coerce')
            df = df.sort_values(by=COL_DATE_DT)

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
        if not self._validate_columns([COL_NET_WORTH]):
            return 0.0
        return self.processed_df[COL_NET_WORTH_PARSED].iloc[-1]

    def get_last_update_date(self) -> str:
        """Get the date of the last update in MM-YYYY format."""
        return self.processed_df[COL_DATE_DT].iloc[-1].strftime(DATE_FORMAT_DISPLAY)

    def get_month_over_month_net_worth_variation_percentage(self) -> float:
        """Get month over month net worth percentage change."""
        if not self._validate_columns([COL_NET_WORTH]):
            return 0.0
        
        df = self.processed_df
        if len(df) < 2:
            return 0.0
            
        current: float = df['net_worth_parsed'].iloc[-1]
        previous: float = df['net_worth_parsed'].iloc[-2]
        
        return (current - previous) / previous if previous != 0 else 0.0
    
    def get_month_over_month_net_worth_variation_absolute(self) -> float:
        """Get month over month net worth absolute change."""
        if not self._validate_columns([COL_NET_WORTH]):
            return 0.0

        df = self.processed_df
        if len(df) < 2:
            return 0.0

        return df['net_worth_parsed'].iloc[-1] - df['net_worth_parsed'].iloc[-2]

    def get_year_over_year_net_worth_variation_percentage(self) -> float:
        """Get year over year net worth percentage change."""
        if not self._validate_columns([COL_NET_WORTH]):
            return 0.0
        
        df = self.processed_df
        if len(df) < MONTHS_LOOKBACK_YEAR:
            return 0.0
            
        current: float = df['net_worth_parsed'].iloc[-1]
        previous_year: float = df['net_worth_parsed'].iloc[-MONTHS_LOOKBACK_YEAR]
        
        return (current - previous_year) / previous_year if previous_year != 0 else 0.0
    
    def get_year_over_year_net_worth_variation_absolute(self) -> float:
        """Get year over year net worth absolute change."""
        if not self._validate_columns([COL_NET_WORTH]):
            return 0.0

        df = self.processed_df
        if len(df) < MONTHS_LOOKBACK_YEAR:
            return 0.0

        return df['net_worth_parsed'].iloc[-1] - df['net_worth_parsed'].iloc[-MONTHS_LOOKBACK_YEAR]

    def get_average_saving_ratio_last_12_months_percentage(self) -> float:
        """Get average saving ratio for last 12 months as percentage."""
        if not self._validate_columns([COL_INCOME, COL_EXPENSES]):
            return 0.0

        df = self.processed_df
        income: float = df[COL_INCOME_PARSED].iloc[-MONTHS_IN_YEAR:].sum()
        expenses: float = df[COL_EXPENSES_PARSED].iloc[-MONTHS_IN_YEAR:].sum()

        return (income - expenses) / income if income != 0 else 0.0

    def get_average_saving_ratio_last_12_months_absolute(self) -> float:
        """Get average monthly savings for last 12 months."""
        if not self._validate_columns([COL_INCOME, COL_EXPENSES]):
            return 0.0

        df = self.processed_df
        income: float = df[COL_INCOME_PARSED].iloc[-MONTHS_IN_YEAR:].sum()
        expenses: float = df[COL_EXPENSES_PARSED].iloc[-MONTHS_IN_YEAR:].sum()

        return (income - expenses) / MONTHS_IN_YEAR if income != 0 else 0.0

    def get_fi_progress(self) -> float:
        """Get FI progress - placeholder implementation."""
        return 0.263

    def get_monthly_net_worth(self) -> Dict[str, List]:
        """Get monthly net worth data for charting."""
        if not self._validate_columns([COL_DATE, COL_NET_WORTH]):
            return {'dates': [], 'values': []}
        
        df = self.processed_df.dropna(subset=[COL_DATE_DT])
        return {
            'dates': df[COL_DATE_DT].dt.strftime(DATE_FORMAT_STORAGE).tolist(),
            'values': df['net_worth_parsed'].tolist()
        }
    def get_assets_liabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get assets and liabilities breakdown from the latest data."""
        asset_liabilities: Dict[str, Dict[str, Any]] = {CATEGORY_ASSETS: {}, CATEGORY_LIABILITIES: {}}
        reference_date = None

        # Use preprocessed DataFrames
        assets_df = self.processed_assets_df
        liabilities_df = self.processed_liabilities_df

        if assets_df is not None and not assets_df.empty:
            # Get latest row
            latest_row = assets_df.iloc[-1]
            reference_date = assets_df[COL_DATE_DT].iloc[-1]

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
                    if category not in asset_liabilities[CATEGORY_ASSETS]:
                        asset_liabilities[CATEGORY_ASSETS][category] = {}
                    asset_liabilities[CATEGORY_ASSETS][category][item] = value
                else:
                    # Single header: column name is the item
                    item = col
                    value = parse_monetary_value(latest_row[col])
                    asset_liabilities[CATEGORY_ASSETS][item] = value

        # Process Liabilities DataFrame
        if liabilities_df is not None and not liabilities_df.empty:
            # Use reference date from Assets to get the corresponding row
            if reference_date is not None:
                matching_rows = liabilities_df[liabilities_df[COL_DATE_DT] <= reference_date]
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
                    if any(keyword in col[0] or keyword in col[1] for keyword in ['Date', 'Data', COL_CATEGORY]):
                        continue
                else:
                    if any(keyword in col for keyword in ['Date', 'Data', COL_CATEGORY]):
                        continue

                if isinstance(col, tuple) and len(col) == 2:
                    # MultiIndex: (category, item)
                    category, item = col
                    category = category.strip()
                    item = item.strip()
                    if not category or category == COL_CATEGORY:
                        continue
                    value = parse_monetary_value(latest_row[col])
                    if category not in asset_liabilities[CATEGORY_LIABILITIES]:
                        asset_liabilities[CATEGORY_LIABILITIES][category] = {}
                    asset_liabilities[CATEGORY_LIABILITIES][category][item] = value
                else:
                    # Single header: column name is the item
                    item = col
                    value = parse_monetary_value(latest_row[col])
                    asset_liabilities[CATEGORY_LIABILITIES][item] = value

        return asset_liabilities
    
    def get_cash_flow_last_12_months(self) -> Dict[str, float]:
        """Get cash flow data for last 12 months."""
        if not self._validate_columns([COL_INCOME]):
            return {CATEGORY_SAVINGS: 0.0, CATEGORY_EXPENSES: 0.0}
        
        if self.processed_expenses_df is None:
            return {CATEGORY_SAVINGS: 0.0, CATEGORY_EXPENSES: 0.0}
        
        # Income from main df
        income = self.processed_df[COL_INCOME_PARSED].iloc[-MONTHS_IN_YEAR:].sum()
        
        # Expenses from expenses df (last 12 months)
        ef: pd.DataFrame = self.processed_expenses_df
        latest_date: pd.Timestamp = ef[COL_DATE_DT].max()
        start_date: pd.Timestamp = (latest_date - pd.DateOffset(months=MONTHS_IN_YEAR-1)).replace(day=1)
        
        ef_last_12: pd.DataFrame = ef[(ef[COL_DATE_DT] >= start_date) & (ef[COL_DATE_DT] <= latest_date)]
        total_expenses: float = ef_last_12[COL_AMOUNT_PARSED].sum()
        
        # Expenses by category
        expenses_by_category: Dict[str, float] = ef_last_12.groupby(COL_CATEGORY)[COL_AMOUNT_PARSED].sum().to_dict()
        
        result: Dict[str, float] = {CATEGORY_EXPENSES: total_expenses, CATEGORY_SAVINGS: income - total_expenses}
        result.update(expenses_by_category)
        
        return result
    
    def get_average_expenses_by_category_last_12_months(self) -> Dict[str, float]:
        """Get average expenses by category for last 12 months."""
        if self.processed_expenses_df is None:
            return {}
        
        ef: pd.DataFrame = self.processed_expenses_df
        latest_date: pd.Timestamp = ef[COL_DATE_DT].max()
        start_date: pd.Timestamp = (latest_date - pd.DateOffset(months=MONTHS_IN_YEAR-1)).replace(day=1)
        
        ef_last_12: pd.DataFrame = ef[(ef[COL_DATE_DT] >= start_date) & (ef[COL_DATE_DT] <= latest_date)]
        return ef_last_12.groupby(COL_CATEGORY)[COL_AMOUNT_PARSED].sum().to_dict()
    
    def get_incomes_vs_expenses(self) -> Dict[str, List]:
        """Get income vs expenses data for charting."""
        if not self._validate_columns([COL_DATE, COL_INCOME, COL_EXPENSES]):
            return {'dates': [], 'incomes': [], 'expenses': []}
        
        df = self.processed_df.dropna(subset=[COL_DATE_DT]).iloc[-MONTHS_IN_YEAR:]
        
        return {
            'dates': df[COL_DATE_DT].dt.strftime(DATE_FORMAT_STORAGE).tolist(),
            'incomes': df[COL_INCOME_PARSED].tolist(),
            'expenses': [-x for x in df[COL_EXPENSES_PARSED].tolist()]  # Negative for chart
        }

