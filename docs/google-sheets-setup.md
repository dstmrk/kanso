# Google Sheets Setup

Kanso uses Google Sheets as its data backend, giving you the flexibility to edit your financial data anywhere while maintaining automatic sync with the dashboard.

## Overview

Kanso expects a Google Sheet with **4 specific tabs**:

1. **Assets** - Your bank accounts, investments, property values
2. **Liabilities** - Mortgages, loans, credit card debt
3. **Incomes** - Salary, freelance, passive income
4. **Expenses** - All your spending with categories

## Prerequisites

- A Google account
- Basic familiarity with Google Sheets
- Google Cloud Console access (for service account)

## Step 1: Create Your Financial Sheet

### Option A: Use the Template (Recommended)

1. **[Open the Kanso Template](https://docs.google.com/spreadsheets/d/1BROgBjWEwFZbelGN31LKcQYpXG7QbPMGkIfmIx3t3SY/copy)** - this opens the copy dialog directly
2. Click **Make a copy** to add it to your Google Drive
3. Copy the sheet URL - you'll need it later

### Option B: Create from Scratch

Create a new Google Sheet with these tabs:

#### Assets Tab Structure

```
| Date    | Cash | Savings | Stocks | Property |
|---------|------|---------|--------|----------|
| 2024-01 | 5000 | 20000   | 15000  | 250000   |
| 2024-02 | 5500 | 21000   | 16000  | 250000   |
```

**Format:**
- First column: `Date` (YYYY-MM format)
- Other columns: Your asset categories (can be multi-level headers)
- Values: Monetary amounts (can include currency symbols: €, $, £)

#### Liabilities Tab Structure

```
| Date    | Mortgage | Car Loan | Credit Card |
|---------|----------|----------|-------------|
| 2024-01 | 200000   | 15000    | 2000        |
| 2024-02 | 199000   | 14500    | 1800        |
```

**Format:**
- Same structure as Assets
- Store as **positive numbers** (Kanso handles the math)

#### Incomes Tab Structure

```
| Date    | Salary | Freelance | Dividends |
|---------|--------|-----------|-----------|
| 2024-01 | 3500   | 500       | 100       |
| 2024-02 | 3500   | 800       | 100       |
```

**Format:**
- First column: `Date` (YYYY-MM format)
- Other columns: Your income sources
- Supports **multi-level headers** for complex income structures

#### Expenses Tab Structure

```
| Date    | Merchant  | Amount | Category     | Type     |
|---------|-----------|--------|--------------|----------|
| 2024-01 | Grocery   | 150.50 | Food         | Variable |
| 2024-01 | Rent      | 1200   | Housing      | Fixed    |
| 2024-01 | Netflix   | 15     | Entertainment| Fixed    |
```

**Required Columns:**
- `Date` - Transaction date (YYYY-MM or YYYY-MM-DD)
- `Merchant` - Store or vendor name
- `Amount` - Transaction amount
- `Category` - Spending category (Food, Housing, Transport, etc.)
- `Type` - `Fixed` or `Variable`

!!! tip "Expense Categories"
    Common categories: Food, Housing, Transport, Entertainment, Healthcare, Education, Shopping, Utilities, Insurance

## Step 2: Create Google Service Account

Kanso uses a **service account** for secure, server-side access to your Google Sheet.

!!! info "Service Account Setup (5 minutes)"
    Follow the official [gspread Service Account guide](https://docs.gspread.org/en/latest/oauth2.html#service-account).

    **Quick overview** - You'll need to:

    1. Create a Google Cloud Project (free)
    2. Enable **Google Sheets API** and **Google Drive API**
    3. Create a service account and download JSON credentials

    **What you'll get**: A JSON file with credentials - keep it safe for the next step!

## Step 3: Share Sheet with Service Account

1. Open your Google Sheet
2. Click the **Share** button (top-right)
3. Paste the service account email:
    - Found in the JSON file as `client_email`
    - Format: `kanso-service-account@your-project.iam.gserviceaccount.com`
4. Set permission to **Editor**
5. Uncheck "Notify people"
6. Click **Share**

## Step 4: Configure Kanso

During the onboarding wizard, you'll need:

1. **Service Account JSON** - The entire content of the downloaded JSON file
2. **Sheet URL** - Your Google Sheet URL (looks like `https://docs.google.com/spreadsheets/d/SHEET_ID/edit`)

### Manual Configuration (Optional)

If you want to configure manually, edit `.env.test` or use the browser's local storage:

```json
{
  "google_credentials_json": "{ \"type\": \"service_account\", \"project_id\": \"...\", ... }",
  "sheet_url": "https://docs.google.com/spreadsheets/d/SHEET_ID/edit"
}
```

## Sheet Tips & Best Practices

### Date Format

- **Monthly tracking**: Use `YYYY-MM` (e.g., `2024-01`)
- **Daily expenses**: Use `YYYY-MM-DD` (e.g., `2024-01-15`)
- Kanso automatically normalizes dates to first day of month

### Currency Symbols

Kanso automatically detects and parses currency symbols. Supported formats include:

| Currency | Symbol | Example     |
|----------|--------|-------------|
| EUR      | €      | € 1.234,56  |
| USD      | $      | $1,234.56   |
| GBP      | £      | £1,234.56   |
| CHF      | Fr     | Fr 1'234.56 |
| JPY      | ¥      | ¥1,234      |
| CAD      | C$     | C$1,234.56  |
| AUD      | A$     | A$1,234.56  |
| CNY      | ¥      | ¥1,234.56   |
| INR      | ₹      | ₹1,234.56   |
| BRL      | R$     | R$ 1.234,56 |

You can mix formats within your sheet - Kanso will detect and parse correctly.

### Multi-Level Headers

For complex asset structures, use multi-level headers:

```
|         | Cash        | Cash        | Investments | Investments |
| Date    | Checking    | Savings     | Stocks      | Bonds       |
|---------|-------------|-------------|-------------|-------------|
| 2024-01 | 2000        | 10000       | 15000       | 5000        |
```

Kanso will automatically detect and process hierarchical columns.

### Data Validation

Add Google Sheets data validation for consistency:

- **Categories**: Dropdown list (Food, Housing, Transport, etc.)
- **Type**: Dropdown with "Fixed" and "Variable"
- **Dates**: Date format validation

## Troubleshooting

### "Failed to access Google Sheet"

**Cause:** Service account doesn't have access

**Fix:**
1. Check that you shared the sheet with the service account email
2. Verify the sheet URL is correct
3. Ensure Google Sheets API is enabled in Google Cloud Console

### "Invalid JSON credentials"

**Cause:** Malformed service account JSON

**Fix:**
1. Re-download the JSON key from Google Cloud Console
2. Copy the **entire** JSON content (including `{` and `}`)
3. Ensure no extra whitespace or line breaks

### "Sheet structure invalid"

**Cause:** Missing required columns or tabs

**Fix:**
1. Verify all 4 tabs exist: Assets, Liabilities, Incomes, Expenses
2. Check that Expenses tab has all required columns: Date, Merchant, Amount, Category, Type
3. Ensure Assets, Liabilities, Incomes have a "Date" column

### Data Not Refreshing

**Cause:** Cache or sync issue

**Fix:**
1. In Kanso, go to Settings
2. Click **Refresh Data**
3. Check the "Last Refresh" timestamp

## Next Steps

- **[Configuration Guide](configuration.md)** - Customize currency and theme
- **[API Reference](api-reference.md)** - Understand data processing
- **[Architecture](architecture.md)** - Learn how Kanso works
