# Kanso – Stop Guessing. Start Knowing.

![GitHub release (latest by date)](https://img.shields.io/github/v/release/dstmrk/kanso)
![CI](https://github.com/dstmrk/kanso/workflows/CI/badge.svg)
[![codecov](https://codecov.io/gh/dstmrk/kanso/branch/main/graph/badge.svg)](https://codecov.io/gh/dstmrk/kanso)
![GitHub](https://img.shields.io/github/license/dstmrk/kanso)

> **Check your financial health in 5 minutes per month.**
> See exactly where your money goes, spot trends before they become problems, and make confident decisions about your finances.

**📚 [Full Documentation](https://dstmrk.github.io/kanso/)** • **[Features Overview](https://dstmrk.github.io/kanso/features/overview/)** • **[Quick Install](https://dstmrk.github.io/kanso/installation/)**

<table>
  <tr>
    <td><img src="docs/images/dashboard_light.png" alt="Light Mode"/></td>
    <td><img src="docs/images/dashboard_dark.png" alt="Dark Mode"/></td>
  </tr>
  <tr>
    <td align="center"><b>Light Mode</b></td>
    <td align="center"><b>Dark Mode</b></td>
  </tr>
</table>

---

## The Problem

**You work hard. You earn money. But at the end of the month...**

- 🤔 **"Where did it all go?"** - Money disappears. You can't pinpoint where.
- 😟 **"Am I on track?"** - No idea if you're making progress or falling behind.
- 📈 **"Is spending getting worse?"** - You suspect it is, but you can't prove it.
- 😫 **"Spreadsheet fatigue"** - Manual calculations, no charts, exhausting.

**The anxiety is real. The control is missing.**

---

## The Solution

**Kanso gives you clarity without complexity.**

### Before Kanso:
- Open 3 spreadsheets to see the full picture
- Calculate net worth manually each month
- Wonder if that Christmas spending was worse than last year
- Feel anxious about money (but can't explain why)

### With Kanso (5 minutes per month):
1. **Open dashboard** → See net worth trend in 10 seconds
2. **Check savings ratio** → Green = doing great, Yellow/Red = time to adjust
3. **Spot spending patterns** → "Oh, I didn't realize I spend that much there"
4. **Make one decision** → Cancel subscription, adjust budget, or celebrate progress

**Result**: Confidence. Control. Calm.

---

## What You Get

### 📊 Answer "Am I on track?" in 10 seconds
Net worth up? ✅ Keep going.
Savings ratio green? ✅ You're doing great.
No spreadsheet archaeology needed.

### 💸 Spot spending patterns before they become problems
Year-over-year comparison reveals lifestyle inflation early.
Merchant breakdown shows where money actually goes.
Fix issues before they compound.

### 📈 Watch your wealth grow (or catch it shrinking)
Stacked bar chart shows exactly where wealth is accumulating.
See assets grow and liabilities shrink over time.
Track progress, not just account balances.

### 🔒 Keep your financial data under your control
Self-hosted on your infrastructure. No bank connections required.
Your data stays in your Google Sheets (or local DB soon).
No cloud service reads your transactions. Ever.

---

## Quick Start

### Option 1: Docker (5 minutes)

```bash
# Download and start
curl -o docker-compose.yml https://raw.githubusercontent.com/dstmrk/kanso/main/docker-compose.yml
docker compose up -d

# Open http://localhost:6789
```

**That's it.** Follow onboarding wizard to connect Google Sheets.

### Option 2: Local Development

```bash
# Clone and install
git clone https://github.com/dstmrk/kanso.git
cd kanso
uv sync

# Run
uv run python main.py

# Open http://localhost:6789
```

📖 **[Detailed Installation Guide](https://dstmrk.github.io/kanso/installation/)** • **[Google Sheets Setup](https://dstmrk.github.io/kanso/google-sheets-setup/)**

---

## How It Works

```
📝 Your Google Sheet → 📊 Kanso Dashboard → ✅ Confident Decisions → 💰 Better Financial Health
```

**Simple**:

1. **Keep data in Google Sheets** (edit anywhere, familiar interface)
2. **Kanso visualizes automatically** (charts, calculations, trends)
3. **You make informed decisions** (no guessing, no anxiety)

---

## Is Kanso For You?

### ✅ You'll Love Kanso If...

- You **already track finances** in spreadsheets (Kanso visualizes what you have)
- You want **visibility without complexity** (4 KPIs, not 50-category budgets)
- You prefer **monthly reviews** over daily transaction tracking
- You value **data ownership** and self-hosting
- You're **comfortable running Docker** (or asking AI to help you)

### ❌ Kanso Might Not Be For You If...

- You need **automatic bank sync** (Kanso doesn't connect to banks)
- You want **envelope budgeting** or strict category limits
- You expect **set-and-forget** automation (Kanso requires monthly data entry)
- You need a **mobile-first app** (Kanso is web-based, mobile-responsive)

**Honest assessment**: Kanso is for people who manually track finances and want better insights, not for people looking to automate everything.

---

## Features

### 📊 Financial Insights
- **Net worth tracking** with asset/liability breakdown over time
- **Savings ratio** monitoring (color-coded: green = healthy, yellow/red = needs attention)
- **Month-over-month** and **year-over-year** comparisons
- **Cash flow** analysis (income vs expenses with automatic calculations)

### 💸 Expense Analysis
- **Year-over-year** spending comparison with forecast
- **Merchant breakdown** (top 80% of spending + "Other")
- **Expense type** analysis (recurring, essential, discretionary)
- **Transaction history** with sorting and pagination

### 🎨 User Experience
- **5-second load** with skeleton placeholders
- **Dark/light mode** toggle with persistent preferences
- **Responsive design** works on desktop, tablet, mobile
- **2-step onboarding** wizard for first-time setup

### 🔐 Data & Privacy
- **Self-hosted** - runs on your infrastructure
- **Google Sheets backend** - your data stays in your control
- **No bank connections** - you input what you want to track
- **Smart caching** - 24h data refresh, manual refresh button available
- **Encrypted storage** - credentials secure in browser storage

### 🧪 Developer Experience
- **322 unit tests** + **17 E2E tests** (comprehensive coverage)
- **Type-safe** with mypy validation
- **Smart CI/CD** - E2E tests run only when UI changes
- **Docker-ready** - production container with multi-stage build
- **Extensive documentation** - architecture, API reference, contributing guide

---

## Real-World Use Cases

**Scenario 1: The "Where did it all go?" Mystery**

**Problem**: You earn €4k/month, but account is always near zero.

**Solution**: Kanso's expense breakdown shows:
- 30% food delivery (you didn't realize)
- €200/month subscriptions (you forgot about)
- Spending grew 15% vs last year (lifestyle inflation)

**Action**: Cook more, cancel 3 subscriptions, save €400/month.

---

**Scenario 2: The Homeowner's Progress Check**

**Problem**: Paying mortgage for 2 years. Am I making progress?

**Solution**: Net worth chart shows:
- Assets (property) stable at €250k
- Liabilities (mortgage) down from €200k → €190k
- Net worth up €10k (it's working!)

**Action**: Stay the course. Consider extra principal payments.

---

**Scenario 3: The Raise That Disappeared**

**Problem**: Got 10% raise last year. Savings didn't increase. Where did money go?

**Solution**: Year-over-year expense comparison shows:
- Spending also up 10% (lifestyle inflation)
- Dining out doubled (celebrating new income)
- Savings ratio unchanged at 15%

**Action**: Freeze lifestyle. Save 100% of next raise.

---

## 🌱 Why "Kanso"?

> *Kanso (簡素)* is a Japanese word meaning **simplicity** and **elimination of the non-essential**.

This is not a tool for daily micro-management. It's for people who want to check in on their finances **once a month**, track big trends, and stay focused on what matters — without noise, stress, or overcomplication.

Your data stays in your Google Sheet. Kanso just makes it beautiful and easy to understand.

---

## 🧩 Tech Stack

**Built for reliability and clarity**:

- **[Python 3.13](https://www.python.org/)** + **[NiceGUI](https://nicegui.io)** - Modern async web UI
- **[pandas](https://pandas.pydata.org/)** + **[gspread](https://github.com/burnash/gspread)** - Data processing and Google Sheets integration
- **[ECharts](https://echarts.apache.org/)** - Interactive data visualizations
- **[Tailwind CSS](https://tailwindcss.com/)** + **[DaisyUI](https://daisyui.com/)** - Modern UI styling
- **[Docker](https://www.docker.com/)** - Self-contained deployment
- **[pytest](https://pytest.org/)** + **[Playwright](https://playwright.dev/)** - Comprehensive testing

**Not blockchain, not AI, not buzzwords. Just clear insights from your data.**

---

## 📂 Project Structure

```bash
kanso/
├── main.py                  # Application entry point
├── app/
│   ├── core/               # Core utilities (validation, caching, monitoring)
│   ├── logic/              # Business logic (financial calculations)
│   ├── services/           # External integrations (Google Sheets)
│   └── ui/                 # UI components (pages, charts, navigation)
├── tests/
│   ├── unit/               # 322 unit tests
│   └── e2e/                # 17 end-to-end tests
├── docs/                   # Documentation (MkDocs)
└── .github/workflows/      # CI/CD pipelines
```

**Clean architecture**: Separation of concerns, testable components, well-documented.

---

## 🧪 Testing

Kanso has a comprehensive test suite covering critical paths:

```bash
# Run unit tests (322 tests, ~6s)
pytest -m "not e2e"

# Run E2E tests (17 tests, ~80s)
playwright install --with-deps chromium
pytest -m e2e --browser chromium

# Run with coverage
pytest -m "not e2e" --cov=app --cov-report=html
```

**CI/CD Strategy**: Smart execution based on changed files
- ✅ **Always**: Unit tests, linting, type checking
- 🎯 **Smart**: E2E tests run on `main` or when UI/service files change
- ⚡ **Fast**: ~2 min for most PRs, ~7 min with E2E

---

## 📚 Documentation

**Comprehensive guides for every use case**:

- **[Features Overview](https://dstmrk.github.io/kanso/features/overview/)** - What can Kanso do?
- **[Dashboard Guide](https://dstmrk.github.io/kanso/features/dashboard/)** - Understand the 4 key metrics
- **[Net Worth Tracking](https://dstmrk.github.io/kanso/features/net-worth/)** - Asset/liability breakdown
- **[Expense Analysis](https://dstmrk.github.io/kanso/features/expenses/)** - Find spending patterns
- **[Installation](https://dstmrk.github.io/kanso/installation/)** - Docker and local setup
- **[Google Sheets Setup](https://dstmrk.github.io/kanso/google-sheets-setup/)** - Prepare your data
- **[Configuration](https://dstmrk.github.io/kanso/configuration/)** - Environment variables
- **[Architecture](https://dstmrk.github.io/kanso/architecture/)** - Technical design
- **[Contributing](https://dstmrk.github.io/kanso/contributing/)** - Development guide

---

## 🛠️ Development

```bash
# Setup
git clone https://github.com/dstmrk/kanso.git
cd kanso
uv sync --all-extras

# Run
uv run python main.py

# Lint
uv run ruff check .
uv run mypy app

# Test
pytest
```

**Contributing**: See **[CONTRIBUTING.md](./CONTRIBUTING.md)** for guidelines.

---

## 🔒 Security

Security is a priority. See **[SECURITY.md](./SECURITY.md)** for:
- Supported versions
- Vulnerability reporting
- Best practices

**Never commit credentials.** Kanso stores them securely in encrypted browser storage.

---

## 📄 License

MIT License - see **[LICENSE](./LICENSE)** for details.

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/dstmrk/kanso/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dstmrk/kanso/discussions)
- **Security**: [SECURITY.md](./SECURITY.md)

---

<p align="center">
  <strong>Ready to stop guessing and start knowing?</strong><br/>
  <a href="https://dstmrk.github.io/kanso/installation/">Get Started in 5 Minutes →</a>
</p>

<p align="center">
  Made with ❤️ and a focus on <em>simplicity</em>
</p>
