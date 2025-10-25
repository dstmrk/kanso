# API Reference

Complete reference for Kanso's core classes, functions, and data models.

## Finance Calculator

### `FinanceCalculator`

Core calculation engine for financial metrics and chart data.

**Location:** `app/logic/finance_calculator.py`

#### Constructor

```python
FinanceCalculator(
    assets_df: pd.DataFrame | None = None,
    liabilities_df: pd.DataFrame | None = None,
    expenses_df: pd.DataFrame | None = None,
    incomes_df: pd.DataFrame | None = None,
)
```

**Parameters:**
- `assets_df` - DataFrame with Date column and asset values
- `liabilities_df` - DataFrame with Date column and liability values
- `expenses_df` - DataFrame with Date, Merchant, Amount, Category, Type columns
- `incomes_df` - DataFrame with Date column and income sources

#### Methods: Net Worth

##### `get_current_net_worth() -> float`

Calculate the most recent net worth (assets - liabilities).

**Returns:** Latest net worth value

**Example:**
```python
calc = FinanceCalculator(assets_df=assets, liabilities_df=liabilities)
net_worth = calc.get_current_net_worth()  # 50000.0
```

##### `get_monthly_net_worth() -> list[dict[str, Any]]`

Get time series of net worth for charting.

**Returns:** List of `{date: str, net_worth: float, ...}` dictionaries

**Example:**
```python
data = calc.get_monthly_net_worth()
# [
#   {"date": "2024-01", "net_worth": 48000.0, ...},
#   {"date": "2024-02", "net_worth": 50000.0, ...},
# ]
```

##### `get_month_over_month_net_worth_variation_percentage() -> float`

Calculate MoM percentage change in net worth.

**Returns:** Percentage change (e.g., 2.5 for +2.5%)

##### `get_month_over_month_net_worth_variation_absolute() -> float`

Calculate MoM absolute change in net worth.

**Returns:** Monetary change (e.g., 1200.0 for €1,200)

##### `get_year_over_year_net_worth_variation_percentage() -> float`

Calculate YoY percentage change in net worth.

**Returns:** Percentage change

##### `get_year_over_year_net_worth_variation_absolute() -> float`

Calculate YoY absolute change in net worth.

**Returns:** Monetary change

#### Methods: Savings

##### `get_average_saving_ratio_last_12_months_percentage() -> float`

Calculate average savings ratio over last 12 months.

**Formula:** `(Income - Expenses) / Income * 100`

**Returns:** Percentage (e.g., 25.5 for 25.5% savings rate)

##### `get_average_saving_ratio_last_12_months_absolute() -> float`

Calculate average monthly savings amount.

**Returns:** Average savings in currency units

#### Methods: Charts

##### `get_cash_flow_last_12_months() -> dict[str, Any]`

Get cash flow data for the past 12 months.

**Returns:** Dictionary with:
- `dates` - List of month labels
- `incomes` - Income values by source
- `expenses` - Total expenses
- `savings` - Net savings

**Example:**
```python
chart_data = calc.get_cash_flow_last_12_months()
# {
#   "dates": ["Jan", "Feb", ...],
#   "incomes": {
#     "Salary": [3000, 3000, ...],
#     "Freelance": [500, 800, ...],
#   },
#   "expenses": [2000, 2200, ...],
#   "savings": [1500, 1600, ...],
# }
```

##### `get_average_expenses_by_category() -> dict[str, Any]`

Get average spending by category (last 12 months).

**Returns:** Dictionary with:
- `categories` - List of category names
- `values` - Average amounts per category

##### `get_incomes_vs_expenses() -> dict[str, Any]`

Compare total income vs expenses (last 12 months).

**Returns:** Dictionary with:
- `categories` - ["Income", "Expenses"]
- `values` - [total_income, total_expenses]

## DataFrame Processor

### `DataFrameProcessor`

Utilities for preprocessing financial DataFrames.

**Location:** `app/logic/dataframe_processor.py`

#### Static Methods

##### `find_date_column(df: pd.DataFrame) -> str | tuple | None`

Find the Date column in single or multi-index DataFrame.

**Returns:** Column name (string or tuple for MultiIndex), or None if not found

**Example:**
```python
col = DataFrameProcessor.find_date_column(df)
# "Date" or ("Date", "") or None
```

##### `sum_monetary_columns_for_row(row: pd.Series, exclude: list[str]) -> float`

Sum all monetary columns in a row, excluding specified patterns.

**Parameters:**
- `row` - DataFrame row as Series
- `exclude` - List of column patterns to skip (e.g., ["Date", "Category"])

**Returns:** Total sum of parsed monetary values

##### `preprocess_expenses(df: pd.DataFrame) -> pd.DataFrame | None`

Preprocess expenses DataFrame with date and amount parsing.

**Transformations:**
- Parse `Date` column to datetime (`date_dt`)
- Parse `Amount` to float (`amount_parsed`)
- Sort by date

**Returns:** Processed DataFrame or None if invalid structure

##### `preprocess_assets(df: pd.DataFrame) -> pd.DataFrame | None`

Preprocess assets DataFrame with date parsing and sorting.

##### `preprocess_liabilities(df: pd.DataFrame) -> pd.DataFrame | None`

Preprocess liabilities DataFrame with date parsing and sorting.

##### `preprocess_incomes(df: pd.DataFrame) -> pd.DataFrame | None`

Preprocess incomes DataFrame with date parsing and sorting.

## Monetary Parsing

### Functions

**Location:** `app/logic/monetary_parsing.py`

##### `detect_currency(value: str) -> str | None`

Detect currency from symbol in string.

**Parameters:**
- `value` - String potentially containing currency symbol

**Returns:** Currency code ("EUR", "USD", etc.) or None

**Example:**
```python
detect_currency("€ 1.234,56")  # "EUR"
detect_currency("$1,234.56")   # "USD"
detect_currency("1234")        # None
```

##### `parse_monetary_value(value: Any, currency: str | None = None) -> float`

Parse monetary value with intelligent currency detection.

**Parameters:**
- `value` - Input value (string, int, float, or None)
- `currency` - Optional currency code to force specific parsing

**Returns:** Parsed float value (0.0 for unparseable values)

**Supported Formats:**

| Currency | Format Example | Parsed Value |
|----------|----------------|--------------|
| EUR      | € 1.234,56     | 1234.56      |
| USD      | $1,234.56      | 1234.56      |
| GBP      | £1,234.56      | 1234.56      |
| CHF      | Fr 1 234,56    | 1234.56      |
| JPY      | ¥1,234         | 1234.0       |

**Example:**
```python
parse_monetary_value("€ 1.234,56")  # 1234.56
parse_monetary_value("$1,234.56")   # 1234.56
parse_monetary_value(1234)          # 1234.0
parse_monetary_value(None)          # 0.0
parse_monetary_value("-")           # 0.0
parse_monetary_value("abc")         # 0.0 (with warning log)
```

## Currency Formats

### `CurrencyFormat`

Immutable currency configuration.

**Location:** `app/core/currency_formats.py`

#### Attributes

```python
@dataclass(frozen=True)
class CurrencyFormat:
    symbol: str                         # Currency symbol (€, $, £, etc.)
    decimal_sep: str                    # Decimal separator ("." or ",")
    thousands_sep: str                  # Thousands separator ("," or ".")
    has_decimals: bool                  # Whether currency uses decimals
    position: Literal["before", "after"] # Symbol position relative to amount
```

#### Constants

##### `CURRENCY_FORMATS: dict[str, CurrencyFormat]`

Pre-configured formats for supported currencies.

**Example:**
```python
from app.core.currency_formats import CURRENCY_FORMATS

eur_format = CURRENCY_FORMATS["EUR"]
# CurrencyFormat(symbol="€", decimal_sep=",", thousands_sep=".", has_decimals=True)
```

#### Functions

##### `get_currency_format(currency: str) -> CurrencyFormat`

Get format configuration for a currency.

**Raises:** `ValueError` if currency not supported

##### `get_currency_symbol(currency: str) -> str`

Get symbol for a currency (with fallback to $ for unknown).

##### `get_supported_currencies() -> list[str]`

Get list of all supported currency codes.

## Finance Service

### `FinanceService`

Service layer for data access and business logic.

**Location:** `app/services/finance_service.py`

#### Methods

##### `get_calculator() -> FinanceCalculator | None`

Get a FinanceCalculator instance with loaded data.

**Returns:** Calculator or None if data loading failed

##### `get_dashboard_data() -> dict[str, Any] | None`

Get all dashboard data (KPIs + charts) in a single call.

**Returns:** Dictionary with `kpi_data` and `chart_data` keys

**Example:**
```python
service = FinanceService()
data = service.get_dashboard_data()

if data:
    kpis = data["kpi_data"]
    charts = data["chart_data"]

    print(f"Net Worth: {kpis['net_worth']}")
    print(f"Charts: {charts.keys()}")
```

## Data Models

### `ExpenseRow`

Validated expense transaction.

**Location:** `app/core/validators.py`

#### Fields

```python
class ExpenseRow(BaseModel):
    date: str        # YYYY-MM or YYYY-MM-DD format
    merchant: str    # Vendor name (non-empty)
    amount: str      # Monetary value with optional currency
    category: str    # Spending category (non-empty)
    type: str        # "Fixed" or "Variable" (non-empty)
```

#### Validators

- `date` - Must be parseable to YYYY-MM format
- `merchant`, `category`, `type` - Must be non-empty after stripping whitespace
- `amount` - Must contain at least one digit

**Example:**
```python
from app.models.validators import ExpenseRow

expense = ExpenseRow(
    date="2024-01",
    merchant="Grocery Store",
    amount="€ 150.50",
    category="Food",
    type="Variable"
)
```

### `AssetRow`, `LiabilityRow`, `IncomeRow`

Similar validation models for other financial data types.

## Constants

### Date Formats

**Location:** `app/core/constants.py`

```python
DATE_FORMAT_STORAGE = "%Y-%m"      # YYYY-MM for monthly data
DATE_FORMAT_DISPLAY = "%m-%Y"     # "01-2025" for UI
```

### Column Names

```python
COL_DATE = "Date"
COL_AMOUNT = "Amount"
COL_CATEGORY = "Category"
COL_MERCHANT = "Merchant"
COL_TYPE = "Type"

COL_DATE_DT = "date_dt"           # Parsed datetime column
COL_AMOUNT_PARSED = "amount_parsed"  # Parsed float column
```

### Financial Thresholds

```python
SAVING_RATIO_THRESHOLD_LOW = 0.2     # 20% - "error" level
SAVING_RATIO_THRESHOLD_MEDIUM = 0.4  # 40% - "warning" level
```

### Time Constants

```python
MONTHS_IN_YEAR = 12
MONTHS_LOOKBACK_YEAR = 13          # 12 months + 1 for YoY comparison
CACHE_TTL_SECONDS = 86400          # 24 hours
```

## Next Steps

- **[Architecture](architecture.md)** - Understand system design
- **[Contributing](contributing.md)** - Contribute to Kanso
- **[Configuration](configuration.md)** - Customize settings
