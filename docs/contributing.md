# Contributing to Kanso

Thank you for your interest in contributing to Kanso! This guide will help you get started.

## Code of Conduct

Be respectful, inclusive, and constructive. We're building this together.

## Ways to Contribute

### 🐛 Report Bugs

Found a bug? [Open an issue](https://github.com/dstmrk/kanso/issues/new?template=bug_report.md) with:

- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Docker version, browser)
- Screenshots or logs (if applicable)

### 💡 Suggest Features

Have an idea? [Start a discussion](https://github.com/dstmrk/kanso/discussions/new?category=ideas) to:

- Explain the use case
- Describe the proposed solution
- Discuss alternatives
- Get community feedback before implementation

### 📚 Improve Documentation

Documentation improvements are always welcome:

- Fix typos or unclear explanations
- Add examples or diagrams
- Improve installation instructions
- Write tutorials or guides

### 🔧 Submit Code

Ready to code? Follow the development workflow below.

## Where to Start?

New to the codebase? Start with issues labeled [`good first issue`](https://github.com/dstmrk/kanso/labels/good%20first%20issue).

These are carefully selected tasks that:

- Don't require deep knowledge of the entire codebase
- Have clear acceptance criteria
- Are mentored by maintainers

Check also [GitHub Discussions](https://github.com/dstmrk/kanso/discussions) for feature ideas and architecture questions.

## Development Setup

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- Docker (for E2E tests)
- Git

### Fork and Clone

1. **Fork** the repository on GitHub
2. **Clone** your fork:

```bash
git clone https://github.com/YOUR_USERNAME/kanso.git
cd kanso
```

3. **Add upstream** remote:

```bash
git remote add upstream https://github.com/dstmrk/kanso.git
```

### Install Dependencies

```bash
# Install all dependencies including dev tools
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install
```

### Environment Setup (Optional)

```bash
# For development, use the dev environment
ln -s .env.dev .env
```

This enables debug mode, hot-reload, and verbose logging.

### Run Locally

```bash
# Start the application
uv run python main.py

# Open http://localhost:9525
```

## Development Workflow

### 1. Create a Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/fixes

### 2. Make Changes

Write clean, well-documented code following our conventions (see below).

### 3. Test Your Changes

```bash
# Run unit tests
uv run pytest tests/unit/ -v

# Run specific test file
uv run pytest tests/unit/test_finance_calculator.py -v

# Run with coverage
uv run pytest tests/unit/ --cov=app --cov-report=term
```

For UI changes, add E2E tests:

```bash
# Install Playwright browsers
uv run playwright install chromium

# Run E2E tests
uv run pytest tests/e2e/ -v --headed
```

### 4. Lint and Format

Pre-commit hooks will run automatically on commit. To run manually:

```bash
# Lint with ruff
uv run ruff check .

# Auto-fix linting issues
uv run ruff check . --fix

# Format with black
uv run black .

# Type check with mypy
uv run mypy app --ignore-missing-imports
```

### 5. Commit Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add savings goal tracking feature

- Created GoalTracker class for milestone tracking
- Added goal progress visualization to dashboard
- Included unit tests for goal calculations
- Updated documentation with usage examples"
```

**Commit message format:**
- First line: Short summary (50 chars max)
- Blank line
- Detailed explanation (wrap at 72 chars)
- Reference issues: `Fixes #123` or `Closes #456`

### 6. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name
```

On GitHub:
1. Open a Pull Request from your branch to `dstmrk/kanso:main`
2. Fill out the PR template
3. Link related issues
4. Wait for CI checks to pass
5. Request review

## Code Style

### Python

- **PEP 8** compliant (enforced by ruff)
- **Type hints** for all function signatures
- **Docstrings** for classes and public methods (Google style)

**Example:**
```python
def calculate_savings_ratio(income: float, expenses: float) -> float:
    """Calculate savings ratio as percentage of income.

    Args:
        income: Total monthly income
        expenses: Total monthly expenses

    Returns:
        Savings ratio as percentage (0-100)

    Raises:
        ValueError: If income is zero or negative
    """
    if income <= 0:
        raise ValueError("Income must be positive")

    return ((income - expenses) / income) * 100
```

### File Organization

```
app/
├── core/          # Constants, config, utilities
├── logic/         # Business logic and calculations
├── models/        # Pydantic models for validation
├── services/      # Data access layer
└── ui/            # UI components and pages

tests/
├── unit/          # Unit tests (mirror app/ structure)
└── e2e/           # End-to-end tests
```

### Naming Conventions

- **Files:** `snake_case.py`
- **Classes:** `PascalCase`
- **Functions/variables:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private:** `_leading_underscore`

## Testing Guidelines

### Unit Tests

- **Location:** `tests/unit/test_<module>.py`
- **Coverage:** Aim for 90%+ on new code
- **Isolation:** Mock external dependencies (Google Sheets, etc.)
- **Pattern:** Arrange-Act-Assert

**Example:**
```python
class TestFinanceCalculator:
    def test_get_current_net_worth(self):
        # Arrange
        assets_df = pd.DataFrame({"Date": ["2024-01"], "Cash": [10000]})
        liabilities_df = pd.DataFrame({"Date": ["2024-01"], "Loan": [5000]})

        # Act
        calc = FinanceCalculator(assets_df=assets_df, liabilities_df=liabilities_df)
        net_worth = calc.get_current_net_worth()

        # Assert
        assert net_worth == 5000.0
```

### E2E Tests

- **Location:** `tests/e2e/test_<page>.py`
- **Purpose:** Test critical user flows
- **Tools:** Playwright for browser automation
- **Tag with:** `@pytest.mark.e2e`

**Example:**
```python
@pytest.mark.e2e
def test_dashboard_loads_with_data(page: Page):
    """Test that dashboard renders without crashing."""
    page.goto("/home")
    expect(page.locator(".main-content")).to_be_visible(timeout=5000)
    assert page.locator('text="Net Worth"').count() > 0
```

### Test Naming

- Descriptive names: `test_<what>_<condition>_<expected>`
- Examples:
  - `test_parse_monetary_value_with_eur_symbol_returns_float`
  - `test_get_net_worth_with_no_data_returns_zero`

## Pull Request Guidelines

### Before Submitting

- ✅ All tests pass locally
- ✅ Pre-commit hooks pass
- ✅ Code is documented
- ✅ CHANGELOG.md updated (if applicable)
- ✅ Breaking changes noted in PR description

### PR Description Template

```markdown
## Description
Brief summary of changes.

## Type of Change
- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] E2E tests added/updated (for UI changes)
- [ ] Tested locally

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Docstrings added/updated
- [ ] Tests pass locally
- [ ] Documentation updated

## Related Issues
Fixes #123
Closes #456
```

### UI Changes

For UI changes, include:
- **Screenshots** (before/after)
- **E2E tests** to prevent regressions
- **Tag with `[e2e]`** in commit message to trigger E2E CI

## CI/CD Pipeline

GitHub Actions runs on every PR:

- ✅ **Lint:** ruff + mypy
- ✅ **Test (Unit):** extensive test coverage
- ✅ **Test (E2E):** Smoke tests (on UI changes)
- ✅ **Docker Build:** Ensure image builds

**Smart E2E:**
- Runs on push to `main`
- Runs on UI file changes
- Runs with `[e2e]` in commit message
- Skips with `[skip e2e]` in commit message

## Release Process

Releases follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (v1.0.0): Breaking changes
- **MINOR** (v0.4.0): New features (backward compatible)
- **PATCH** (v0.3.1): Bug fixes

### Versioning (Maintainers Only)

1. Update `CHANGELOG.md`
2. Tag release: `git tag v0.4.0`
3. Push tag: `git push --tags`
4. GitHub Actions builds and publishes Docker image

## Project Structure

```
kanso/
├── .github/
│   └── workflows/       # CI/CD pipelines
├── app/
│   ├── core/           # Utilities and constants
│   ├── logic/          # Business logic
│   ├── models/         # Data models
│   ├── services/       # Data access layer
│   └── ui/             # UI components
├── docs/               # MkDocs documentation
├── static/             # CSS, images, themes
├── tests/
│   ├── unit/           # Unit tests
│   └── e2e/            # End-to-end tests
├── .env.dev            # Development environment config
├── .env.prod           # Production environment config
├── docker-compose.yml  # Docker orchestration
├── Dockerfile          # Container image
├── mkdocs.yml          # Documentation config
├── pyproject.toml      # Project metadata
├── uv.lock             # Locked dependencies
└── README.md           # Project overview
```

## Getting Help

- **Questions:** [GitHub Discussions](https://github.com/dstmrk/kanso/discussions)
- **Bugs:** [GitHub Issues](https://github.com/dstmrk/kanso/issues)
- **Real-time chat:** _(coming soon)_

## Recognition

Contributors are recognized in:

- README.md Contributors section
- GitHub Contributors page
- Release notes

Thank you for contributing to Kanso! 🎉
