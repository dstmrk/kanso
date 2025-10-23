# CI/CD Workflows

## Overview

This directory contains GitHub Actions workflows for continuous integration and deployment.

## Workflows

### `ci.yml` - Main CI Pipeline

Runs tests, linting, and builds on every push and PR.

#### Jobs

1. **changes** - Detects which files changed (for smart job execution)
2. **test** - Unit tests (skips on docs-only or static-only, ~2 min)
3. **lint** - Code quality checks (skips on docs-only or static-only, ~1 min)
4. **test-e2e** - E2E tests (smart conditional, always validates static changes, ~5 min)
5. **docker** - Docker build validation (skips on docs-only, always validates static changes, ~2 min)

#### Performance Optimizations ⚡

- **Docs-only skip**: All jobs skip when only `.md`, `docs/`, or `LICENSE` files change
- **Static-only skip**: `test` and `lint` skip when only `static/**` files change (E2E and Docker still run to validate visual changes)
- **Dependency caching**: `uv` dependencies are cached using GitHub Actions cache
- **Smart E2E**: E2E tests run only when UI/services change or on main branch

#### Smart Job Execution 🎯

All CI jobs use intelligent conditions to run only when needed:

| Trigger | Test/Lint | E2E | Docker | Why |
|---------|-----------|-----|--------|-----|
| Push to `main` (code changes) | ✅ Yes | ✅ Yes | ✅ Yes | Protect production |
| Push to `main` (docs only) | ⚡ Skip | ⚡ Skip | ⚡ Skip | No code/UI impact |
| Push to `main` (static only) | ⚡ Skip | ✅ Yes | ✅ Yes | Validate visual changes |
| PR with code changes | ✅ Yes | ✅ If UI changed | ✅ Yes | Standard validation |
| PR with docs only (`.md`, `LICENSE`) | ⚡ Skip | ⚡ Skip | ⚡ Skip | No code/UI impact |
| PR with static only (`static/**`) | ⚡ Skip | ✅ If UI changed | ✅ Yes | Logo/favicon/theme validation |
| PR with `app/ui/` changes | ✅ Yes | ✅ Yes | ✅ Yes | UI changes need E2E |
| PR with `app/services/` changes | ✅ Yes | ✅ Yes | ✅ Yes | Backend affects UI |
| Commit with `[e2e]` | ✅ Yes | ✅ Force | ✅ Yes | Manual override |
| Commit with `[skip e2e]` | ✅ Yes | ❌ Skip | ✅ Yes | Skip only E2E |
| Manual trigger | ✅ Yes | ✅ Yes | ✅ Yes | On-demand testing |

#### Docs-Only Detection

Files that trigger docs-only skip (all jobs skip):
```yaml
- '**.md'              # All markdown files
- 'docs/**'            # Documentation directory
- 'LICENSE'            # License file
- '.github/**/*.md'    # GitHub docs
```

#### Static-Only Detection

Files that trigger static-only skip (test/lint skip, E2E/Docker run):
```yaml
- 'static/**'          # Favicon, logo, themes (visual assets need E2E validation)
```

**Why E2E still runs?** Static files (logo, favicon, themes) affect the visual appearance of the UI, so E2E tests validate that they render correctly.

#### File Patterns Triggering E2E

```yaml
- 'app/ui/**'         # UI components
- 'app/services/**'   # Backend services
- 'tests/e2e/**'      # E2E test files
- 'main.py'           # App entry point
- '.env.test'         # Test configuration
- 'pyproject.toml'    # Dependencies
```

## Usage

### Run E2E Tests Manually

1. Go to **Actions** tab
2. Select **CI** workflow
3. Click **Run workflow**

### Force E2E on Specific Commit

```bash
git commit -m "Update backend logic [e2e]"
```

### Skip E2E (Use with Caution)

```bash
git commit -m "Fix typo [skip e2e]"
```

## Local Testing

```bash
# Unit tests only (fast)
pytest -m "not e2e"

# E2E tests only
pytest -m e2e --browser chromium

# All tests
pytest --browser chromium
```

## Maintenance

- **Unit tests**: Run on all code changes (skip on docs-only or static-only)
- **E2E tests**: Run when UI/services/static change or on main branch (skip on docs-only)
- **Lint**: Run on all code changes (skip on docs-only or static-only)
- **Docker**: Run on all code/static changes (skip on docs-only)
- **Docs-only changes**: All jobs skipped to save CI resources
- **Static-only changes**: Only E2E and Docker run to validate visual changes

### CI Resource Optimization

Smart skip features save significant CI time:

| Change Type | Time Saved | What Runs |
|-------------|-----------|-----------|
| Docs only (`.md`, `LICENSE`) | ~10 min → 0 min | Nothing (all jobs skip) |
| Static only (`static/**`) | ~10 min → ~7 min | Only E2E + Docker (visual validation) |
| Code changes | Full validation | All jobs run |

Applies to **all branches** including `main` to maximize resource savings.

## See Also

- [E2E Test Setup Guide](../../docs/E2E_TEST_SETUP.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)
