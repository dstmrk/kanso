# CI/CD Workflows

## Overview

This directory contains GitHub Actions workflows for continuous integration and deployment.

## Workflows

### `ci.yml` - Main CI Pipeline

Runs tests, linting, and builds on every push and PR.

#### Jobs

1. **changes** - Detects which files changed (for smart job execution)
2. **test** - Unit tests (runs only if code changed, ~2 min)
3. **lint** - Code quality checks (runs only if code changed, ~1 min)
4. **test-e2e** - E2E tests (smart conditional, ~5 min)
5. **docker** - Docker build validation (runs if code or static changed, ~2 min)

#### Performance Optimizations ⚡

- **Smart path filtering**: Jobs run based on what changed
  - `code`: Everything except docs and static assets
  - `static`: Only static assets (images, logos, themes)
  - `ui`: UI-specific files (for E2E smart logic)
- **Docs-only skip**: All jobs skip when only `.md`, `docs/`, or `LICENSE` files change
- **Static-only skip**: `test` and `lint` skip, but E2E and Docker run (visual validation)
- **Dependency caching**: `uv` dependencies are cached using GitHub Actions cache
- **Smart E2E**: E2E tests run when code/static/UI changes or on main branch

#### Smart Job Execution 🎯

All CI jobs use intelligent conditions based on path filters:

| Files Changed | Test | Lint | E2E | Docker | Why |
|---------------|------|------|-----|--------|-----|
| Only `README.md` | ⚡ Skip | ⚡ Skip | ⚡ Skip | ⚡ Skip | Docs-only, no impact |
| Only `ROADMAP.md` + `LICENSE` | ⚡ Skip | ⚡ Skip | ⚡ Skip | ⚡ Skip | Docs-only, no impact |
| Only `static/logo.svg` | ⚡ Skip | ⚡ Skip | ✅ Yes | ✅ Yes | Visual validation needed |
| `app/ui/header.py` | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | Code change |
| `app/ui/header.py` + `README.md` | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | Code change (docs ignored) |
| `main.py` + `ROADMAP.md` | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | Code change |
| `styles.py` + `logo.svg` | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | Code + static |
| `pyproject.toml` | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | Dependency change |
| Push to `main` (any code) | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | Always protect main |
| Commit with `[skip e2e]` | ✅ Yes | ✅ Yes | ❌ Skip | ✅ Yes | Manual E2E skip |
| Commit with `[e2e]` | ✅ Yes | ✅ Yes | ✅ Force | ✅ Yes | Force E2E run |
| Manual trigger | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | On-demand testing |

**Key principle**: If ANY code file changes (even mixed with docs), all code validation runs.

#### Path Filter Definitions

The workflow uses three filters to determine which jobs to run:

**1. Code Filter** (triggers test/lint/e2e/docker):
```yaml
code:
  - '**'               # Match everything
  - '!**.md'           # Except markdown files
  - '!docs/**'         # Except docs directory
  - '!LICENSE'         # Except license
  - '!.github/**/*.md' # Except GitHub markdown
  - '!static/**'       # Except static assets
```

**2. Static Filter** (triggers e2e/docker, skips test/lint):
```yaml
static:
  - 'static/**'        # Images, logos, themes, favicons
```

**3. UI Filter** (for E2E smart logic):
```yaml
ui:
  - 'app/ui/**'        # UI components
  - 'app/services/**'  # Backend services affecting UI
  - 'tests/e2e/**'     # E2E test files
  - 'main.py'          # App entry point
  - '.env.test'        # Test configuration
  - 'pyproject.toml'   # Dependencies
```

**Why E2E runs for static?** Visual assets (logo, favicon, themes) affect UI appearance and need visual validation.

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

- **Unit tests**: Run when `code` filter matches (any non-docs, non-static file)
- **Lint**: Run when `code` filter matches (any non-docs, non-static file)
- **E2E tests**: Run when `code` OR `static` filter matches (visual validation)
- **Docker**: Run when `code` OR `static` filter matches (container validation)

### CI Resource Optimization

Smart path filtering saves significant CI time:

| Change Type | Time Saved | What Runs | Reason |
|-------------|-----------|-----------|--------|
| Docs only (`.md`, `LICENSE`) | ~10 min → 0 min | Nothing | No code/UI impact |
| Static only (`static/**`) | ~10 min → ~7 min | E2E + Docker only | Visual validation needed |
| Code + docs (`header.py` + `README.md`) | Full validation | All jobs | Code validation needed |
| Code only (`app/ui/header.py`) | Full validation | All jobs | Standard validation |

**Key improvement**: Mixed changes (code + docs) now correctly trigger all code validation jobs.

Applies to **all branches** including `main` to maximize resource savings.

## See Also

- [E2E Test Setup Guide](../../docs/E2E_TEST_SETUP.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)
