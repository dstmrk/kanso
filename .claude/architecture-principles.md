# Architecture Principles

> **Purpose**: Document architectural decisions, patterns, and technical constraints that guide Kanso's development.

---

## Core Architecture

### Clean Architecture Pattern

Kanso follows **separation of concerns** with clear layer boundaries:

```
app/
├── core/          # Utilities (validation, caching, monitoring)
│   └── No business logic, no external dependencies
├── logic/         # Business logic (financial calculations)
│   └── Pure functions, testable, no UI/service coupling
├── services/      # External integrations (Google Sheets, future: SQLite)
│   └── Data fetching, no business logic
└── ui/            # User interface (NiceGUI components)
    └── No business logic, orchestrates core/logic/services
```

**Key principle**: Dependency flow is **unidirectional**:
- `ui` → `logic` → `core`
- `ui` → `services` → `logic`
- Never: `logic` → `ui` or `services` → `ui`

---

## Design Principles

### 1. Simplicity First

**Philosophy**: Kanso stays simple. Features must serve the core use case: **monthly financial check-ins**.

**Implications**:
- Reject features that add daily complexity
- Optimize for monthly usage (not daily micro-management)
- Prefer clarity over sophistication
- "When in doubt, leave it out"

### 2. Data Ownership

**Philosophy**: Users own their data. Kanso is a **view layer** on top of user-controlled data sources.

**Implications**:
- Google Sheets backend (user controls data in their Google Drive)
- Future: SQLite local storage (user controls data on their disk)
- No proprietary data formats
- Export functionality always available
- No vendor lock-in

### 3. Privacy by Design

**Philosophy**: Financial data is private. Self-hosting is a first-class use case.

**Implications**:
- No telemetry by default
- No cloud service required (self-hosted works standalone)
- Credentials stored locally (browser storage, not server)
- No data sent to Kanso developers/servers

### 4. Progressive Complexity

**Philosophy**: Start simple, grow when needed.

**Implications**:
- Basic features work out of the box
- Advanced features opt-in (not forced)
- Onboarding is 2 steps (credentials + sheet URL)
- Power users can extend via future plugin system

---

## Technical Patterns

### Async-First

**Rule**: All I/O operations must be async.

**Why**: NiceGUI is async-native. Blocking I/O freezes the UI.

**Examples**:
```python
# ✅ Good
async def fetch_data() -> pd.DataFrame:
    async with aiohttp.ClientSession() as session:
        ...

# ❌ Bad
def fetch_data() -> pd.DataFrame:
    response = requests.get(url)  # Blocks event loop!
```

### Type Hints Everywhere

**Rule**: All functions, methods, and variables should have type hints.

**Why**: Catches bugs early, improves IDE experience, serves as documentation.

**Examples**:
```python
# ✅ Good
def calculate_savings_ratio(income: float, expenses: float) -> float:
    if income == 0:
        return 0.0
    return ((income - expenses) / income) * 100

# ❌ Bad
def calculate_savings_ratio(income, expenses):
    return ((income - expenses) / income) * 100
```

**Enforcement**: `mypy` runs in CI. No PR merges with type errors.

### Dependency Injection

**Rule**: Don't instantiate dependencies inside functions. Pass them as parameters.

**Why**: Testability, flexibility, clear contracts.

**Examples**:
```python
# ✅ Good
async def load_dashboard_data(
    data_source: DataSource,
    cache: Cache
) -> DashboardData:
    ...

# ❌ Bad
async def load_dashboard_data() -> DashboardData:
    sheets_client = GoogleSheetsClient()  # Hard-coded dependency!
    ...
```

### Pure Business Logic

**Rule**: Business logic in `app/logic/` must be pure functions (no side effects, no external dependencies).

**Why**: Easy to test, easy to reason about, reusable.

**Examples**:
```python
# ✅ Good (in app/logic/finance_calculator.py)
def calculate_net_worth(
    assets: pd.DataFrame,
    liabilities: pd.DataFrame
) -> float:
    total_assets = assets['amount'].sum()
    total_liabilities = liabilities['amount'].sum()
    return total_assets - total_liabilities

# ❌ Bad (mixing logic with service calls)
async def calculate_net_worth(sheet_id: str) -> float:
    client = GoogleSheetsClient()
    assets = await client.fetch_assets(sheet_id)
    ...
```

---

## Testing Strategy

### Test Pyramid

```
      /\
     /E2E\      ← Few (17 tests, critical user paths)
    /------\
   / Unit  \    ← Many (322 tests, all logic)
  /----------\
```

**Principles**:
1. **Unit tests dominate**: Fast, isolated, cover all business logic
2. **E2E tests are selective**: Only critical paths (onboarding, dashboard load, navigation)
3. **No integration tests** (yet): Services are thin wrappers, unit + E2E sufficient

### What to Test

#### ✅ Always Write Unit Tests For:
- **Business logic** (`app/logic/`)
- **Core utilities** (`app/core/`)
- **Data transformations**
- **Financial calculations**
- **Edge cases** (zero values, negative numbers, empty data)

#### ⚠️ E2E Tests Only For:
- **Critical user paths**:
  - Onboarding flow
  - Dashboard load and display
  - Navigation between pages
  - Data refresh
- **When UI changes** (detected by CI path filtering)

#### ❌ Don't Write Tests For:
- **UI layout** (unless it breaks functionality)
- **Styling changes** (visual regression out of scope)
- **Third-party library behavior** (trust the library)

### Test Structure

**Follow AAA pattern**: Arrange, Act, Assert

```python
def test_calculate_savings_ratio():
    # Arrange
    income = 5000.0
    expenses = 3500.0

    # Act
    ratio = calculate_savings_ratio(income, expenses)

    # Assert
    assert ratio == 30.0
```

### Test Naming

**Pattern**: `test_<function>_<scenario>_<expected_outcome>`

**Examples**:
```python
def test_calculate_savings_ratio_positive_income_returns_correct_percentage():
    ...

def test_calculate_savings_ratio_zero_income_returns_zero():
    ...

def test_calculate_savings_ratio_expenses_exceed_income_returns_negative():
    ...
```

---

## CI/CD Strategy

### Smart Test Execution

**Philosophy**: Run tests relevant to changes, not everything always.

**Implementation**:
- **Always**: Unit tests, linting (`ruff`), type checking (`mypy`)
- **Conditionally**: E2E tests
  - When: `main` branch OR UI/service files changed
  - Why: E2E tests are slow (~80s), run only when needed

### Path-Based Triggers

E2E tests run if any of these paths change:
```yaml
- 'app/ui/**'
- 'app/services/**'
- 'tests/e2e/**'
- 'main.py'
```

**Rationale**: Logic changes don't break UI. UI changes might break E2E.

### No Flaky Tests

**Rule**: If a test is flaky (passes/fails randomly), fix or delete it immediately.

**Why**: Flaky tests erode trust in CI. Better to have no test than a flaky one.

---

## Code Organization

### File Structure Conventions

#### Logic Files (app/logic/)
- **One concern per file**: `finance_calculator.py`, `expense_analyzer.py`, `net_worth_tracker.py`
- **Pure functions only**: No async, no I/O, no side effects
- **Descriptive names**: Function names explain what they calculate

#### Service Files (app/services/)
- **One external system per file**: `google_sheets.py`, `data_loader.py`
- **Async methods**: All external calls must be async
- **Thin wrappers**: Minimal logic, just fetch/transform/return

#### UI Files (app/ui/)
- **One page per file**: `dashboard.py`, `expenses.py`, `net_worth.py`
- **Reusable components**: `header.py`, `charts.py`, `navigation.py`
- **No business logic**: Orchestrate calls to logic/services, don't calculate

### Import Organization

**Order**: Standard library → Third-party → Local

```python
# ✅ Good
import asyncio
from typing import Dict, List

import pandas as pd
from nicegui import ui

from app.core.cache import Cache
from app.logic.finance_calculator import calculate_net_worth
from app.services.data_loader import load_financial_data
```

**Enforcement**: `ruff` checks import order.

---

## Data Flow Patterns

### Standard Data Flow

```
User Action (UI)
    ↓
Service fetches raw data (Google Sheets)
    ↓
Logic transforms/calculates (pure functions)
    ↓
UI displays results (charts, tables)
```

**Example**:
```python
# 1. User clicks "Refresh" in UI
async def on_refresh_click():
    # 2. Service fetches
    raw_data = await data_loader.refresh_all_data()

    # 3. Logic calculates
    net_worth = calculate_net_worth(
        raw_data['assets'],
        raw_data['liabilities']
    )

    # 4. UI displays
    net_worth_card.update(f"€{net_worth:,.2f}")
```

### Caching Strategy

**Rule**: Cache expensive operations (Google Sheets API calls) with 24h TTL.

**Implementation**:
- Cache at service layer (not UI, not logic)
- Manual refresh button bypasses cache
- Cache stored in-memory (no persistence needed)

**Example**:
```python
@cached(ttl_hours=24)
async def fetch_sheet_data(sheet_id: str) -> pd.DataFrame:
    ...
```

---

## Performance Considerations

### Lazy Loading

**Rule**: Load data only when needed, not upfront.

**Example**: Dashboard loads overview first, detail pages load on navigation.

### Skeleton States

**Rule**: Show skeleton placeholders while loading (not blank screen or spinners).

**Why**: Users perceive faster load times with visual feedback.

### Batch Operations

**Rule**: When possible, fetch multiple sheets in parallel (not sequentially).

**Example**:
```python
# ✅ Good (parallel)
assets, liabilities, income, expenses = await asyncio.gather(
    fetch_assets(),
    fetch_liabilities(),
    fetch_income(),
    fetch_expenses()
)

# ❌ Bad (sequential)
assets = await fetch_assets()
liabilities = await fetch_liabilities()
...
```

---

## Error Handling

### User-Facing Errors

**Rule**: Show actionable error messages, not stack traces.

**Bad**: `KeyError: 'assets'`

**Good**: "Could not find 'Assets' sheet. Please check your Google Sheet has a tab named 'Assets'."

### Error Boundaries

**Pattern**: Catch errors at UI boundary, log details, show friendly message.

```python
try:
    data = await load_dashboard_data()
except GoogleSheetsError as e:
    logger.error(f"Failed to load data: {e}")
    ui.notify("Could not connect to Google Sheets. Check your credentials.", type="negative")
except Exception as e:
    logger.exception("Unexpected error loading dashboard")
    ui.notify("Something went wrong. Please try again.", type="negative")
```

---

## Security Principles

### Credentials Storage

**Current**: Browser localStorage (encrypted by browser)

**Future (v0.8.0+)**:
- Local mode: No credentials needed (SQLite)
- Google Sheets mode: Service account JSON (user-provided)

### No Secrets in Code

**Rule**: Never commit credentials, API keys, or secrets.

**Enforcement**:
- `.gitignore` covers common secret files
- CI checks for common secret patterns

### Input Validation

**Rule**: Validate all external input (sheet URLs, credentials, user input).

**Where**: `app/core/validators.py`

---

## Refactoring Guidelines

### When to Refactor

**Good reasons**:
- Code is duplicated 3+ times
- Function is >50 lines
- Logic is mixed with UI/services
- Tests are hard to write

**Bad reasons**:
- "I don't like the style"
- "Let me try a new pattern"
- Premature optimization

### Refactoring Process

1. **Write tests first** (if not already covered)
2. **Refactor** in small, logical commits
3. **Verify tests still pass**
4. **No behavior changes** (refactor = same input/output, better structure)

---

## Deprecation Policy

### Pre-v1.0 (Current)

**Policy**: No stability guarantees. Breaking changes allowed with notice in CHANGELOG.

### Post-v1.0 (Future)

**Policy**:
- Stable API, no breaking changes in v1.x
- Deprecated features get 2-version warning period
- Clear migration guides for breaking changes

---

## Future Architecture Changes

### Planned: Abstract DataSource Interface (v0.8.0)

**Goal**: Support multiple backends (Google Sheets, SQLite, future: PostgreSQL)

**Design**:
```python
class DataSource(ABC):
    @abstractmethod
    async def fetch_assets(self) -> pd.DataFrame:
        ...

    @abstractmethod
    async def fetch_liabilities(self) -> pd.DataFrame:
        ...

# Implementations
class GoogleSheetsDataSource(DataSource):
    ...

class SQLiteDataSource(DataSource):
    ...
```

### Planned: Plugin System (v2.0.0)

**Goal**: Extensibility without bloating core

**Design**:
- Base `KansoPlugin` interface
- Plugins can add widgets, API routes, data sources
- Sandboxed execution with permission system

---

## Dos and Don'ts

### ✅ Dos

- **Keep business logic pure** (no side effects)
- **Use type hints everywhere**
- **Write unit tests for all logic**
- **Handle errors gracefully** (user-friendly messages)
- **Document non-obvious decisions** (code comments for "why", not "what")
- **Keep functions small** (<50 lines ideal)
- **Use async for I/O** (always)
- **Follow existing patterns** (consistency over personal preference)

### ❌ Don'ts

- **Don't put logic in UI components**
- **Don't use sync I/O** (blocks event loop)
- **Don't skip type hints** (mypy will catch you)
- **Don't test third-party code**
- **Don't commit secrets**
- **Don't write flaky tests** (fix or delete)
- **Don't optimize prematurely** (profile first)
- **Don't mix concerns** (one file, one responsibility)

---

## Questions to Ask Before Adding Code

1. **Does this serve the core use case?** (Monthly financial check-ins)
2. **Is this the simplest approach?**
3. **Where does this belong?** (core/logic/services/ui)
4. **Can I test this easily?** (If no, refactor)
5. **Does this have proper type hints?**
6. **Have I handled errors gracefully?**
7. **Is this documented?** (If non-obvious)

---

_This guide evolves as we learn. Update when architectural decisions change._
