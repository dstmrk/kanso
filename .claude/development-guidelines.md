# Development Guidelines

> **Purpose**: Practical guidelines for day-to-day development, testing, commits, and collaboration.

---

## Getting Started

### Prerequisites

- **Python 3.13+**
- **uv** (fast package manager)
- **Docker** (for container testing)
- **Git**

### Initial Setup

```bash
# Clone
git clone https://github.com/dstmrk/kanso.git
cd kanso

# Install dependencies
uv sync --all-extras

# Run locally
uv run python main.py

# Open browser
# http://localhost:6789
```

---

## Development Workflow

### Daily Development Loop

```bash
# 1. Make changes to code

# 2. Run linter (auto-fix)
uv run ruff check . --fix

# 3. Run type checker
uv run mypy app

# 4. Run unit tests
uv run pytest -m "not e2e" -v

# 5. (If UI changes) Run E2E tests
uv run pytest -m e2e -v --browser chromium

# 6. Commit with conventional format
git add .
git commit -m "feat: add new chart component"
```

### Hot Reload

**NiceGUI has auto-reload**: Changes to Python files trigger automatic browser refresh.

**No manual restart needed** during development (unless changing dependencies).

---

## Code Style

### Formatting: ruff

**Enforcement**: CI fails if code isn't formatted.

**Auto-fix locally**:
```bash
uv run ruff check . --fix
uv run ruff format .
```

**Config**: `pyproject.toml` (already configured)

### Type Checking: mypy

**Enforcement**: CI fails on type errors.

**Check locally**:
```bash
uv run mypy app
```

**Rule**: All functions must have type hints.

**Example**:
```python
# ✅ Good
def calculate_ratio(a: float, b: float) -> float:
    return a / b if b != 0 else 0.0

# ❌ Bad (no type hints)
def calculate_ratio(a, b):
    return a / b if b != 0 else 0.0
```

### Import Order

**Pattern**: Standard library → Third-party → Local

**Enforcement**: `ruff` checks automatically.

**Example**:
```python
import asyncio
from typing import Optional

import pandas as pd
from nicegui import ui

from app.core.cache import Cache
from app.logic.finance_calculator import calculate_net_worth
```

---

## Testing

### Running Tests

```bash
# All unit tests (fast, ~6 seconds)
uv run pytest -m "not e2e" -v

# Specific file
uv run pytest tests/unit/test_finance_calculator.py -v

# Specific test
uv run pytest tests/unit/test_finance_calculator.py::test_net_worth_calculation -v

# All E2E tests (slow, ~80 seconds)
playwright install --with-deps chromium
uv run pytest -m e2e -v --browser chromium

# With coverage report
uv run pytest -m "not e2e" --cov=app --cov-report=html
```

### Writing Unit Tests

**Location**: `tests/unit/`

**Naming**: `test_<module_name>.py`

**Structure**:
```python
import pytest
from app.logic.finance_calculator import calculate_net_worth

def test_calculate_net_worth_positive_values():
    # Arrange
    assets = pd.DataFrame({'amount': [1000, 2000]})
    liabilities = pd.DataFrame({'amount': [500]})

    # Act
    result = calculate_net_worth(assets, liabilities)

    # Assert
    assert result == 2500
```

**Fixtures**: Use `conftest.py` for reusable test data.

### Writing E2E Tests

**Location**: `tests/e2e/`

**When to write**:
- New critical user path
- Major UI change
- Bug that wasn't caught by unit tests

**Structure**:
```python
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
def test_dashboard_loads_successfully(page: Page):
    # Navigate
    page.goto("http://localhost:6789")

    # Assert critical elements present
    expect(page.locator("text=Net Worth")).to_be_visible()
    expect(page.locator("text=Savings Ratio")).to_be_visible()
```

**Run locally**:
```bash
# Start app in background
uv run python main.py &

# Run E2E tests
uv run pytest -m e2e -v

# Kill app
pkill -f "python main.py"
```

### ⚠️ CRITICAL: Always Update Tests After Changes

**When you change UI flows, features, or add functionality, ALWAYS update both unit and E2E tests.**

**Common scenarios requiring test updates**:

1. **Onboarding flow changes**:
   - Changed step order → Update `tests/e2e/test_onboarding.py`
   - Added/removed steps → Update all test navigation sequences
   - Changed field names/labels → Update locators in E2E tests

2. **Settings page changes**:
   - Added configuration options → Update `tests/e2e/test_user_settings.py`
   - Changed validation logic → Update validation tests

3. **New currencies/options**:
   - Added currencies → Update `tests/unit/test_currency_formats.py`
   - Changed count expectations → Update assertions (e.g., `assert len == 10`)

4. **API/business logic changes**:
   - New calculations → Add unit tests
   - Changed return types → Update all dependent tests
   - New validation rules → Add validation tests

**Test update checklist**:
```bash
# 1. Identify affected test files
grep -r "old_feature_name" tests/

# 2. Update unit tests
# - Add tests for new functionality
# - Update expectations for changed behavior
# - Add new test cases for edge cases

# 3. Update E2E tests
# - Update navigation sequences
# - Update element locators (text, IDs, classes)
# - Update assertions for new UI elements

# 4. Run tests locally
uv run pytest -m "not e2e" -v  # Unit tests
uv run pytest -m e2e -v        # E2E tests

# 5. Fix failures
# - Don't ignore test failures
# - Update tests to match new behavior
# - Ensure all tests pass before committing
```

**Example: v0.6.0 Currency Support Changes**

When we added 5 new currencies and reorganized onboarding:

1. ✅ Updated `test_currency_formats.py`:
   - Changed `assert len == 5` → `assert len == 10`
   - Added tests for CAD, AUD, CNY, INR, BRL
   - Updated all currency iteration loops

2. ✅ Updated `test_onboarding.py`:
   - Added Step 2 (Currency Selection) navigation
   - Updated all test flows: Step 1 → Step 2 (Currency) → Step 3 (Sheets)
   - Updated element locators ("Currency Preference" instead of "Credentials")

3. ✅ Updated `test_user_settings.py`:
   - Updated fixture to include currency step in onboarding
   - Ensured all tests using `setup_user` fixture work correctly

**Why this is critical**:
- ❌ Without test updates: CI fails, blocks merges
- ❌ Ignoring failures: Technical debt, false confidence
- ✅ With test updates: Confidence in changes, regression prevention

### Test Coverage

**Target**: 90%+ for business logic (app/logic/, app/core/)

**Not required**: UI files (hard to unit test, covered by E2E)

**View coverage**:
```bash
uv run pytest -m "not e2e" --cov=app --cov-report=html
open htmlcov/index.html
```

---

## Git Workflow

### Branching Strategy

**Main branch**: `main` (protected)

**Feature branches**: `feat/<feature-name>`

**Bug fixes**: `fix/<bug-description>`

**Example**:
```bash
git checkout -b feat/add-transaction-table
# ... make changes ...
git commit -m "feat: add sortable transaction table"
git push origin feat/add-transaction-table
# Open PR on GitHub
```

### Commit Messages

**Format**: Conventional Commits

```
<type>: <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code restructure (no behavior change)
- `test`: Adding/updating tests
- `chore`: Maintenance (deps, CI, build, etc.)
- `style`: Formatting (no logic change)
- `perf`: Performance improvement

**Examples**:
```
feat: add year-over-year expense comparison chart

Implemented cumulative monthly spending comparison between current and previous year with forecast line.

Closes #42
```

```
fix: handle division by zero in savings ratio calculation

When income is zero, savings ratio now returns 0.0 instead of throwing ZeroDivisionError.
```

```
docs: update installation guide with Docker Compose steps
```

### Pull Request Process

1. **Create feature branch**
2. **Make changes** (follow guidelines above)
3. **Ensure tests pass** locally
4. **Push and open PR**
5. **CI runs automatically**:
   - Linting (ruff)
   - Type checking (mypy)
   - Unit tests
   - E2E tests (if UI/service files changed)
6. **Review** (self-review or collaborator)
7. **Merge** (squash and merge)

### PR Title Format

**Same as commit messages**: `<type>: <description>`

**Examples**:
- `feat: add transaction filtering by date range`
- `fix: correct net worth calculation for negative liabilities`
- `docs: add troubleshooting section to README`

### PR Description Template

```markdown
## What

Brief description of changes.

## Why

Motivation for the change.

## How

Technical approach (if non-obvious).

## Testing

How you tested the change.

## Screenshots (if UI change)

Before/after screenshots.

## Checklist

- [ ] Tests pass locally
- [ ] Added/updated unit tests
- [ ] Added/updated E2E tests (if UI change)
- [ ] Documentation updated (if needed)
- [ ] No secrets/credentials committed
```

---

## CI/CD

### GitHub Actions Workflows

#### CI Workflow (`.github/workflows/ci.yml`)

**Triggers**: Push to any branch, PR to main

**Smart Path Filtering Strategy**:

CI uses path filters to skip unnecessary jobs and save time:

| Files Changed | Unit Tests | Lint | E2E Tests | Docker Build |
|---------------|------------|------|-----------|--------------|
| `app/`, `tests/`, `main.py`, `pyproject.toml` | ✅ Run | ✅ Run | ✅ (if UI changed) | ✅ Run |
| `docs/`, `.claude/`, `README.md`, `mkdocs.yml` | ❌ Skip | ❌ Skip | ❌ Skip | ❌ Skip |
| `static/**` (images, logos) | ❌ Skip | ❌ Skip | ✅ Run | ✅ Run |
| `Dockerfile`, `docker-compose.yml` | ❌ Skip | ❌ Skip | ❌ Skip | ✅ Run |

**Why this strategy?**
- Documentation-only changes don't need code tests (saves ~2-7 min)
- E2E tests only run when UI/services change (slow, ~80s)
- Docker builds only when image might change

**Steps**:
1. **Always runs** (if code changes):
   - Lint (ruff)
   - Type check (mypy)
   - Unit tests

2. **Conditionally runs** (E2E tests):
   - When: Push to `main` OR changes in `app/ui/`, `app/services/`, `tests/e2e/`, `main.py`, `static/`
   - Why: E2E tests are slow, only run when UI might break

3. **Conditionally runs** (Docker build):
   - When: Changes in code, static assets, or infrastructure files
   - Why: Only rebuild image if contents changed

**Local equivalent**:
```bash
uv run ruff check .
uv run mypy app
uv run pytest -m "not e2e"
```

#### Docker Build Workflow

**Triggers**: Push to `main`, tags

**Output**: Docker image pushed to `ghcr.io/dstmrk/kanso:latest`

### CI Best Practices

**✅ Dos**:
- Fix CI failures immediately (don't let them pile up)
- Keep CI fast (<5 min for unit tests, <10 min with E2E)
- Add `[e2e]` tag to PR title if you want to force E2E run

**❌ Don'ts**:
- Don't disable CI checks to "just merge"
- Don't commit without running tests locally first
- Don't write flaky tests (if test is flaky, fix or delete)

---

## Local Development Tips

### Running in Docker Locally

```bash
# Build image
docker build -t kanso:local .

# Run container
docker run -p 6789:8080 kanso:local

# Open browser
# http://localhost:6789
```

### Debugging

**NiceGUI debugging**:
- Add `print()` statements (appear in terminal)
- Use `ui.notify()` for user-visible messages
- Check browser console for JavaScript errors

**Python debugging**:
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or with ipdb (better interface)
import ipdb; ipdb.set_trace()
```

### Performance Profiling

**For slow functions**:
```python
import time

start = time.time()
result = slow_function()
print(f"Took {time.time() - start:.2f}s")
```

**For comprehensive profiling**:
```bash
python -m cProfile -o profile.stats main.py
# Analyze with snakeviz
uv pip install snakeviz
snakeviz profile.stats
```

---

## Dependencies

### Managing Dependencies

**Add dependency**:
```bash
# Add to pyproject.toml
uv add pandas

# Sync environment
uv sync
```

**Add dev dependency**:
```bash
uv add --dev pytest
```

**Update all dependencies**:
```bash
uv sync --upgrade
```

### Dependency Philosophy

**Minimize dependencies**: Only add if:
1. Saves significant development time
2. Well-maintained and popular
3. Not easily implemented in 50 lines

**Avoid dependencies for**:
- Simple utilities (write them)
- Unmaintained packages
- Packages with large footprints (unless critical)

---

## Documentation

### When to Update Docs

**Update documentation when**:
- Adding user-facing feature
- Changing setup/installation process
- Fixing common user issues

**Don't update for**:
- Internal refactoring (no user impact)
- Test changes
- Minor bug fixes (unless affects user workflow)

### Documentation Structure

```
docs/
├── index.md              # Landing page (benefit-driven)
├── features/             # What users can achieve
│   ├── overview.md
│   ├── dashboard.md
│   ├── net-worth.md
│   └── expenses.md
├── installation.md       # How to install
├── google-sheets-setup.md # Data source setup
├── configuration.md      # Environment variables
├── architecture.md       # Technical design
└── contributing.md       # Contribution guide
```

### Documentation Style

**See**: [.claude/documentation-style.md](./documentation-style.md) for comprehensive guide.

**Quick rules**:
- Lead with user benefits (not feature lists)
- Use real-world examples
- Be honest about limitations
- No exact counts (test numbers, LOC, etc.)

### Building Docs Locally

```bash
# Install docs dependencies
uv sync --all-extras

# Serve locally
uv run mkdocs serve

# Open browser
# http://127.0.0.1:8000
```

---

## Common Tasks

### Add a New Chart

1. **Create logic** (if needed):
   ```python
   # app/logic/chart_data.py
   def prepare_chart_data(df: pd.DataFrame) -> dict:
       ...
   ```

2. **Add chart component**:
   ```python
   # app/ui/charts.py
   def render_my_chart(data: dict) -> None:
       chart = ui.echart({
           'xAxis': {'type': 'category', 'data': data['labels']},
           'yAxis': {'type': 'value'},
           'series': [{'type': 'bar', 'data': data['values']}]
       })
   ```

3. **Integrate in page**:
   ```python
   # app/ui/dashboard.py
   chart_data = prepare_chart_data(df)
   render_my_chart(chart_data)
   ```

4. **Write tests**:
   ```python
   # tests/unit/test_chart_data.py
   def test_prepare_chart_data():
       ...
   ```

5. **Document** (if user-facing):
   - Update `docs/features/dashboard.md`
   - Add screenshot (optional)

### Add a New Page

1. **Create UI file**:
   ```python
   # app/ui/new_page.py
   from nicegui import ui

   async def render_new_page():
       with ui.column().classes('w-full'):
           ui.label('New Page').classes('text-2xl font-bold')
           # ... content
   ```

2. **Add navigation**:
   ```python
   # app/ui/navigation.py
   ui.link('New Page', '/new-page')
   ```

3. **Register route**:
   ```python
   # main.py
   from app.ui.new_page import render_new_page

   @ui.page('/new-page')
   async def new_page():
       await render_header()
       await render_new_page()
   ```

4. **Write E2E test**:
   ```python
   # tests/e2e/test_navigation.py
   @pytest.mark.e2e
   def test_new_page_accessible(page: Page):
       page.goto("http://localhost:6789")
       page.click("text=New Page")
       expect(page.locator("text=New Page")).to_be_visible()
   ```

### Refactor a Module

1. **Write tests first** (if not already covered)
2. **Run tests**: Establish baseline (all passing)
3. **Refactor** in small commits
4. **Run tests** after each commit
5. **Verify behavior unchanged**:
   - Unit tests pass
   - E2E tests pass (if UI affected)
   - Manual smoke test
6. **Document** (if interface changed)

---

## Security

### Credentials

**Never commit**:
- Service account JSON files
- API keys
- Passwords
- `.env` files with secrets

**Use**:
- `.gitignore` (already configured)
- Environment variables
- Browser storage (for user credentials)

### Secrets Scanning

**CI checks** for common secret patterns.

**If you accidentally commit secrets**:
1. Rotate the credentials immediately
2. Use `git filter-branch` or BFG Repo-Cleaner to remove from history
3. Force push (if private repo)

### Input Validation

**Always validate**:
- Sheet URLs (must be valid Google Sheets URL)
- User input (no SQL injection risk, but validate format)
- File uploads (future: check MIME types)

**Location**: `app/core/validators.py`

---

## Performance

### Optimization Guidelines

**Premature optimization is evil**:
1. Profile first (find actual bottleneck)
2. Optimize only if measurable impact
3. Maintain readability

**Common bottlenecks**:
- Google Sheets API calls (use caching)
- Large dataframe operations (use vectorized pandas)
- Sync I/O in async functions (always use async)

### Caching Strategy

**Current**: In-memory cache with 24h TTL

**Implementation**: `@cached` decorator in `app/core/cache.py`

**Usage**:
```python
from app.core.cache import cached

@cached(ttl_hours=24)
async def fetch_expensive_data() -> pd.DataFrame:
    ...
```

**Manual refresh**: Bypass cache when user clicks "Refresh"

---

## Troubleshooting

### Common Issues

#### "ModuleNotFoundError"

**Solution**: Sync dependencies
```bash
uv sync
```

#### "Port 6789 already in use"

**Solution**: Kill existing process
```bash
# Find process
lsof -i :6789

# Kill it
kill -9 <PID>
```

#### E2E Tests Fail Locally

**Solution**: Install Playwright browsers
```bash
playwright install --with-deps chromium
```

#### mypy Errors

**Solution**: Add type hints
```python
# Before
def foo(x):
    return x + 1

# After
def foo(x: int) -> int:
    return x + 1
```

---

## Release Process

**Current**: Manual releases (pre-v1.0)

**Steps**:
1. Update version in `pyproject.toml`
2. Update `ROADMAP.md` (move completed version) - **Note**: ROADMAP.md is internal, not committed to main
3. Create release notes file (e.g., `RELEASE_NOTES_v0.5.0.md`)
4. Create git tag: `git tag v0.5.0`
5. Push tag: `git push origin v0.5.0`
6. CI builds and pushes Docker image
7. Create GitHub release manually:
   - Copy content from RELEASE_NOTES_v0.x.x.md
   - Paste into GitHub release UI
   - Delete RELEASE_NOTES file locally (don't commit it)

**Important**:
- ❌ **Don't commit** `RELEASE_NOTES_*.md` files
- ✅ **Do create** them temporarily for copying to GitHub
- ✅ **Do delete** them after release is published
- **Why**: Release notes are managed via GitHub Releases UI, not in repo

**Future**: Automated semantic versioning post-v1.0

---

## Getting Help

### Internal Resources

- [.claude/project-context.md](./project-context.md) - Project overview
- [.claude/architecture-principles.md](./architecture-principles.md) - Technical decisions
- [.claude/documentation-style.md](./documentation-style.md) - Writing guidelines
- [ROADMAP.md](../ROADMAP.md) - Product roadmap

### External Resources

- **NiceGUI docs**: https://nicegui.io
- **pandas docs**: https://pandas.pydata.org
- **ECharts examples**: https://echarts.apache.org/examples

### Community

- **GitHub Issues**: Bug reports
- **GitHub Discussions**: Questions, ideas
- **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## Dos and Don'ts Summary

### ✅ Always Do

- Run tests before committing
- **Update tests when changing UI flows or features** (see Testing section)
- Use type hints on all functions
- Write unit tests for business logic
- Follow conventional commit format
- Keep PRs small and focused
- Update docs for user-facing changes
- Ask for help when stuck

### ❌ Never Do

- Commit secrets/credentials
- Disable CI to force merge
- Write code without tests (for logic)
- Use sync I/O in async functions
- Make breaking changes without discussion
- Document exact counts (they go stale)

---

_These guidelines evolve. Suggest improvements via PR or discussion._
