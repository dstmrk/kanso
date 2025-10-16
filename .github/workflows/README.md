# CI/CD Workflows

## Overview

This directory contains GitHub Actions workflows for continuous integration and deployment.

## Workflows

### `ci.yml` - Main CI Pipeline

Runs tests, linting, and builds on every push and PR.

#### Jobs

1. **changes** - Detects which files changed (for smart E2E strategy)
2. **test** - Unit tests (always runs, ~2 min)
3. **lint** - Code quality checks (always runs, ~1 min)
4. **test-e2e** - E2E tests (smart conditional, ~5 min)
5. **docker** - Docker build validation (always runs, ~2 min)

#### Smart E2E Strategy 🎯

E2E tests use intelligent conditions to run only when needed:

| Trigger | E2E Runs? | Why |
|---------|-----------|-----|
| Push to `main` | ✅ Always | Protect production |
| PR with `app/ui/` changes | ✅ Auto | UI changes need E2E |
| PR with `app/services/` changes | ✅ Auto | Backend changes affect UI |
| PR with docs only | ⚡ Skip | No UI impact |
| Commit with `[e2e]` | ✅ Force | Manual override |
| Commit with `[skip e2e]` | ❌ Skip | Emergency bypass |
| Manual trigger | ✅ Always | On-demand testing |

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

- **Unit tests**: Always run to ensure code quality
- **E2E tests**: Run when UI/services change to catch regressions
- **Lint**: Ensures code style consistency

## See Also

- [E2E Test Setup Guide](../../docs/E2E_TEST_SETUP.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)
