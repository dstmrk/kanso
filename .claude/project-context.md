# Project Context

> **Purpose**: High-level overview of Kanso for maintaining context across sessions.

---

## What is Kanso?

**Kanso** (簡素 - Japanese for "simplicity") is a **self-hosted personal finance dashboard** that helps people answer one question:

> **"Am I on track?"**

It visualizes financial data from Google Sheets (or local SQLite in future) to provide clarity without complexity.

**Not a budgeting app**. Not a transaction tracker. Not envelope budgeting.

**It's a monthly check-in tool** for people who manually track finances and want better insights.

---

## Core Philosophy

### 1. Simplicity (Kanso 簡素)

**Principle**: Eliminate the non-essential. Focus on what matters.

**Application**:
- 4 key metrics (not 50 categories)
- Monthly check-ins (not daily micro-management)
- Clear insights (not data overload)

### 2. User Data Ownership

**Principle**: Your data stays in your control.

**Application**:
- Self-hosted (runs on your infrastructure)
- Google Sheets backend (your data in your Google Drive)
- No cloud service reads your transactions
- Export anytime, no lock-in

### 3. Calm Technology

**Principle**: Insights without anxiety.

**Application**:
- No notifications
- No daily tracking pressure
- No gamification manipulation
- Just clear, actionable information

---

## Target User

### ✅ Who Kanso is For

- **Already tracks finances** in spreadsheets manually
- Wants **visibility without complexity** (high-level trends, not micro-budgets)
- Prefers **monthly reviews** over daily transaction tracking
- Values **data ownership** and self-hosting
- Comfortable running Docker (or asking AI for help)

### ❌ Who Kanso is NOT For

- Needs **automatic bank sync** (Kanso doesn't connect to banks)
- Wants **envelope budgeting** or strict category limits
- Expects **set-and-forget** automation (Kanso requires manual data entry)
- Needs **mobile-first app** (Kanso is web-based, mobile-responsive but desktop-optimized)

---

## Use Case

**Typical workflow**:
1. **Once a month**: User updates Google Sheet with transactions (5-10 minutes)
2. **Open Kanso dashboard**: See net worth, savings ratio, spending trends (30 seconds)
3. **Make one decision**: Cancel subscription, adjust spending, or celebrate progress
4. **Done**: Close dashboard, return to life

**Result**: Confidence about financial health without daily stress.

---

## Tech Stack

### Core Technologies

- **Python 3.13**: Modern async support
- **NiceGUI**: Async web framework built on FastAPI
- **pandas**: Data processing and analysis
- **gspread**: Google Sheets API integration
- **ECharts**: Interactive charting library
- **Tailwind CSS + DaisyUI**: Modern UI styling

### Infrastructure

- **Docker**: Self-contained deployment
- **pytest + Playwright**: Comprehensive testing (unit + E2E)
- **GitHub Actions**: CI/CD with smart test execution
- **MkDocs Material**: Documentation site (hosted on GitHub Pages)

### Development Tools

- **uv**: Fast Python package manager
- **ruff**: Fast linting and formatting
- **mypy**: Static type checking

---

## Project Structure

```
kanso/
├── main.py                  # Application entry point
├── app/
│   ├── core/               # Utilities (validation, caching, monitoring)
│   ├── logic/              # Business logic (financial calculations)
│   ├── services/           # External integrations (Google Sheets)
│   └── ui/                 # UI components (pages, charts, navigation)
├── tests/
│   ├── unit/               # Unit tests (fast, isolated)
│   └── e2e/                # End-to-end tests (critical paths only)
├── docs/                   # MkDocs documentation
│   ├── features/           # Detailed feature guides
│   └── *.md                # Installation, configuration, etc.
├── .claude/                # AI context files (this directory!)
└── ROADMAP.md              # Product roadmap (public)
```

**Architecture**: Clean separation of concerns (core/logic/services/ui)

---

## Current State

### Version: v0.5.0

**Completed Features**:
- ✅ Core financial tracking (income, expenses, assets, liabilities)
- ✅ Interactive dashboard with 4 KPIs + 5 charts
- ✅ Google Sheets integration with 24h smart caching
- ✅ Multi-currency support (EUR, USD, GBP, CHF, JPY)
- ✅ Dark/light mode toggle with persistence
- ✅ Advanced visualizations:
  - Net worth evolution (stacked bar chart)
  - Year-over-year spending comparison with forecast
  - Merchant breakdown (donut chart, top 80% + Other)
  - Expense type analysis (recurring, essential, discretionary)
- ✅ Benefit-driven documentation (README, docs/features/)
- ✅ Docker deployment with pre-built images
- ✅ Comprehensive testing (unit + E2E)
- ✅ Smart CI/CD (path-based test execution)

### Next Focus: v0.6.0 - Data Tables & UI Improvements

**Planned**:
- Sortable/filterable transaction tables
- CSV export functionality
- UI cleanup (drawer consolidation, settings page redesign)
- Auto theme detection (system dark mode)
- Expanded currency support

**See**: [ROADMAP.md](../ROADMAP.md) for full roadmap.

---

## Key Metrics (for internal reference only)

**These numbers are for context. Never document exact counts externally.**

- **Test coverage**: ~322 unit tests, ~17 E2E tests (as of v0.5.0)
- **Load time**: <5 seconds with skeleton states
- **Code size**: ~10,000 lines (excluding tests)
- **Docker image**: ~850 MB (target: <500 MB in v0.6.0)

**Why track privately?**: These change frequently. Documenting them creates maintenance burden.

---

## Development Workflow

### Typical Feature Development

1. **Plan**: Create TODO list of sub-tasks
2. **Test first**: Write unit tests for new logic
3. **Implement**: Code in appropriate layer (core/logic/services/ui)
4. **Type check**: Ensure mypy passes
5. **Lint**: Run ruff
6. **Test**: Verify unit tests pass
7. **E2E** (if UI changes): Write/update E2E tests
8. **Document**: Update relevant docs (if user-facing change)
9. **Commit**: Conventional commit message
10. **PR**: CI runs, review, merge

### Commit Message Format

**Pattern**: `<type>: <description>`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code restructure (no behavior change)
- `test`: Adding/updating tests
- `chore`: Maintenance (deps, CI, etc.)

**Examples**:
- `feat: add year-over-year expense comparison chart`
- `fix: handle zero income in savings ratio calculation`
- `docs: update installation guide with Docker instructions`
- `refactor: extract expense analysis to separate module`

---

## External Dependencies

### Critical Dependencies

- **NiceGUI**: UI framework (async-native, FastAPI-based)
- **pandas**: Data manipulation (financial calculations rely on it)
- **gspread**: Google Sheets API wrapper
- **ECharts**: Charting library (via NiceGUI integration)

### Future Considerations

- **SQLite**: Local storage backend (planned v0.8.0)
- **Plugin system**: Extensibility framework (planned v2.0.0)

---

## Documentation Strategy

**Two audiences**:
1. **End users**: Need to understand what Kanso does for them (benefit-driven)
2. **Developers**: Need to understand how to contribute (architecture, patterns)

**Structure**:
- **README.md**: Benefit-driven landing page (users + developers)
- **docs/**: User-facing documentation (features, installation, setup)
  - `docs/features/`: Deep dives on what users can achieve
  - `docs/installation.md`, `docs/configuration.md`: Getting started
- **docs/architecture.md**: Technical design (for contributors)
- **docs/contributing.md**: How to contribute (for developers)
- **.claude/**: Internal context (for AI-assisted development)

**See**: [.claude/documentation-style.md](./documentation-style.md) for detailed writing guidelines.

---

## Common Patterns

### Financial Calculations

**Location**: `app/logic/finance_calculator.py`

**Pattern**: Pure functions, no side effects

**Example**:
```python
def calculate_net_worth(
    assets: pd.DataFrame,
    liabilities: pd.DataFrame
) -> float:
    return assets['amount'].sum() - liabilities['amount'].sum()
```

### Data Loading

**Location**: `app/services/data_loader.py`

**Pattern**: Async functions, cached with 24h TTL

**Example**:
```python
@cached(ttl_hours=24)
async def fetch_assets(sheet_id: str) -> pd.DataFrame:
    return await google_sheets_client.read_sheet(sheet_id, 'Assets')
```

### UI Components

**Location**: `app/ui/`

**Pattern**: NiceGUI components, orchestrate logic/services

**Example**:
```python
async def render_dashboard():
    data = await data_loader.load_dashboard_data()
    net_worth = calculate_net_worth(data['assets'], data['liabilities'])
    ui.label(f'Net Worth: €{net_worth:,.2f}')
```

---

## Testing Philosophy

### Test What Matters

**Focus on**:
- Business logic correctness
- Edge cases (zero values, empty data, negatives)
- Critical user paths (onboarding, dashboard load)

**Don't focus on**:
- UI layout (unless it breaks functionality)
- Third-party library behavior
- Styling minutiae

### Test Pyramid

- **Base**: Many fast unit tests (logic, core utilities)
- **Middle**: (No integration tests yet - services are thin wrappers)
- **Top**: Few slow E2E tests (critical paths only)

**See**: [.claude/architecture-principles.md](./architecture-principles.md) for detailed testing guidelines.

---

## Deployment

### Current: Docker

**Image**: `ghcr.io/dstmrk/kanso:latest`

**Usage**:
```bash
docker compose up -d
```

**Data persistence**: None currently (credentials in browser storage)

### Future: Dual Mode (v0.8.0)

**Basic Mode**: SQLite local storage (Docker volume)

**Advanced Mode**: Google Sheets (current implementation)

---

## Community & Support

- **GitHub**: https://github.com/dstmrk/kanso
- **Issues**: Bug reports, feature requests
- **Discussions**: General questions, ideas
- **Documentation**: https://dstmrk.github.io/kanso/

**License**: MIT (open source)

---

## Design Decisions (Historical)

### Why NiceGUI?

**Decision**: Use NiceGUI instead of React/Vue + REST API

**Reasoning**:
- Single language (Python frontend + backend)
- Async-native (fits data fetching model)
- Fast prototyping for solo developer
- No complex build pipeline

**Trade-off**: Less ecosystem than React, but faster development

### Why Google Sheets?

**Decision**: Start with Google Sheets backend (not local DB)

**Reasoning**:
- Users already familiar with Sheets
- Multi-device editing without Kanso running
- No data migration needed (users already track there)
- Zero vendor lock-in (user controls data)

**Trade-off**: Requires service account setup, but v0.8.0 adds SQLite option

### Why Self-Hosted Only?

**Decision**: No cloud SaaS offering (yet)

**Reasoning**:
- Financial data is private
- Self-hosting aligns with data ownership philosophy
- Avoids scaling costs/complexity for solo maintainer

**Future**: v2.0.0 may add optional hosted version (self-hosting still supported)

---

## Roadmap Summary

**Current**: v0.5.0 (Advanced Visualizations) ✅

**Next**: v0.6.0 (Data Tables & UI Improvements)

**Path to v1.0**:
- v0.6.0: Data tables + UI cleanup
- v0.7.0: Data editing from UI
- v0.8.0: Dual storage mode (SQLite + Google Sheets)
- v0.9.0: CSV import/export
- v0.10.0: Polish & performance
- v1.0.0: Official release (Q3 2025)

**Post-v1.0**: Extended currency support, community requests, multi-language (i18n)

**Long-term (v2.0.0)**: Plugin system, hosted SaaS option, internationalization

**See**: [ROADMAP.md](../ROADMAP.md) for detailed version plans.

---

## Working with AI (Claude)

### Context Files

**These files** (.claude/*.md) exist to maintain consistency across long conversations and context windows.

**Usage**:
1. AI reads these files at session start or when needed
2. Provides guardrails for architecture, documentation style, etc.
3. Reduces repeated explanations

### When to Update Context Files

**Update when**:
- Major architectural decisions change
- New patterns emerge
- Documentation approach evolves
- Common mistakes need prevention

**Don't update for**:
- Minor refactorings
- Feature additions (those go in code/docs, not context)
- Temporary experiments

---

_This context guide evolves with the project. Update when fundamental aspects change._
