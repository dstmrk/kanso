# Project Architecture & Technology Stack: A Comprehensive Overview

## 1. Vision

The goal is to build a modern, open-source (MIT license) data analysis and visualization application. The platform's cornerstone feature is its extensibility, allowing a community of third-party developers to create and distribute "plugins" that seamlessly integrate with the main application. The architecture is designed to be robust, scalable, and maintainable, prioritizing a clean separation of concerns, a high-quality codebase, and a superior developer experience.

## 2. Core Technology Stack

This stack is a curated collection of mature, best-in-class tools covering the entire development lifecycle, from coding and testing to deployment.

| Category                | Technology                                         | Rationale                                                                      |
| :---------------------- | :------------------------------------------------- | :----------------------------------------------------------------------------- |
| **Backend Framework**   | **FastAPI** (with `uv` for package management)     | High-performance, modern, async-native, with automatic API documentation.      |
| **Database & ORM**      | **SQLite** + **SQLAlchemy**                        | Simple, zero-config persistence. Each plugin gets its own isolated database file. Lightweight and perfect for self-hosted personal finance applications. |
| **Backend Testing**     | **Pytest** + **HTTPX**                             | The de-facto standard for writing clean, scalable tests for Python applications. |
| **Backend Code Quality**| **Ruff**                                           | An all-in-one, high-speed linter and formatter for maintaining a clean Python codebase. |
| **Frontend Framework**  | **React** (bundled with **Webpack 5**)             | The industry standard for data-intensive applications with a vast ecosystem. Webpack chosen for mature Module Federation support. |
| **Frontend Module Federation** | **Webpack 5 Module Federation**            | Production-proven micro-frontend solution for dynamic plugin loading with excellent documentation and tooling. |
| **Frontend Routing**    | **React Router**                                   | The standard library for client-side routing in React applications.              |
| **Server State Mgmt**   | **TanStack Query**                                 | Crucial for fetching, caching, and syncing server data. Reduces boilerplate and improves UX. |
| **Client State Mgmt**   | **React Context**                                  | Built-in React solution for simple global UI state (theme, preferences). Sufficient for Kanso's needs. |
| **UI Components**       | **shadcn/ui** + **Tailwind CSS**                   | A modern, accessible, and themeable component system for rapid UI development. |
| **Data Visualization**  | **TanStack Table v8** + **Apache ECharts**         | Best-in-class libraries for building powerful, interactive tables and charts.  |
| **Frontend Testing**    | **Jest** + **React Testing Library**               | Industry standard for testing React applications with Webpack.          |
| **Frontend Code Quality**| **ESLint** + **Prettier**                          | For maintaining consistent, error-free, and high-quality frontend code.       |
| **Containerization**    | **Docker** & **Docker Compose**                    | For creating a reproducible, isolated, and scalable multi-service environment.   |

## 3. Plugin Architecture

The platform's extensibility is its core feature. A plugin is a self-contained package that can extend the backend, database, and frontend.

### 3.1. General Principles

*   **Plugin as a Package**: A plugin is a standard, installable Python package.
*   **The Plugin Contract**: Each plugin must adhere to a strict structure, including a `pyproject.toml` with specific entry points, a frontend directory with a valid Vite configuration (including Module Federation), and an Alembic directory for database migrations.

### 3.2. Backend Integration

*   **Discovery via Entry Points**: The main application uses Python's `importlib.metadata` to discover installed plugins that declare a specific entry point in their `pyproject.toml`.
    ```toml
    # In the plugin's pyproject.toml
    [project.entry-points."my_app.plugins"]
    plugin_id = "my_plugin_package.main:plugin_router"
    ```
*   **Dynamic Routing**: For each discovered plugin, the main FastAPI application will dynamically mount its `APIRouter` object under a dedicated path, e.g., `/api/plugins/plugin_id/`.

### 3.3. Data Access Model

**Core Principle**: Plugins NEVER access the core database directly. All data access happens via well-defined HTTP API endpoints exposed by the core application.

#### 3.3.1. Plugin Database (Isolated Write)

Each plugin has its own SQLite database for storing plugin-specific data:

```
/data/
  ├── core.db              # Core application only (never accessed by plugins)
  ├── plugin_fire.db       # FI/RE Calculator plugin (full read/write access)
  ├── plugin_stocks.db     # Stocks plugin (full read/write access)
  └── plugin_budget.db     # Budget Tracker plugin (full read/write access)
```

Plugins have **full control** over their own database:
- Define schema as needed
- Use Alembic for migrations (optional) or simple SQL schema files
- Store plugin-specific state, calculations, configurations

#### 3.3.2. Core Data Access (Read via API)

Plugins read core financial data by calling HTTP API endpoints exposed by the core application:

```python
# Example: Plugin accessing core data via API
from kanso_sdk import CoreAPI

async def calculate_fire_scenario():
    # Fetch investment assets from core API
    assets_response = await CoreAPI.get("/api/v1/assets", params={
        "type": "investment"
    })
    assets = assets_response["data"]

    # Fetch expenses for the last 12 months
    expenses_response = await CoreAPI.get("/api/v1/expenses", params={
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    })
    expenses = expenses_response["data"]

    # Calculate with data from plugin's own DB
    total_assets = sum(a["value"] for a in assets)
    monthly_expenses = sum(e["amount"] for e in expenses) / 12

    return {
        "fire_number": monthly_expenses * 12 * 25,  # 4% rule
        "current_progress": total_assets / (monthly_expenses * 12 * 25)
    }
```

#### 3.3.3. Core API Categories

The core application exposes two categories of API endpoints:

**1. Raw Data Endpoints** - Direct access to financial data tables:
```python
GET /api/v1/assets              # All assets (bank accounts, investments, real estate)
GET /api/v1/liabilities         # All liabilities (loans, mortgages, credit cards)
GET /api/v1/income              # Income records
GET /api/v1/expenses            # Expense transactions

# All endpoints support filtering, pagination, date ranges
GET /api/v1/expenses?category=food&start_date=2024-01-01&limit=100
```

**2. Aggregated Analytics Endpoints** - Pre-calculated for performance:
```python
GET /api/v1/analytics/net-worth-timeline    # Historical net worth over time
GET /api/v1/analytics/expense-breakdown     # Expenses grouped by category
GET /api/v1/analytics/income-vs-expenses    # Monthly income vs expenses comparison
```

Plugins use whichever endpoint best fits their needs. Aggregated endpoints are more efficient when plugins need summarized data.

#### 3.3.4. Benefits of API-Only Access

| Aspect | Direct DB Access | API-Only Access ✅ |
|--------|------------------|-------------------|
| **Security** | Plugin sees entire schema | Core controls data exposure |
| **Versioning** | Schema coupling, breaks on changes | API versioned (v1, v2), backward compatible |
| **Performance** | Plugin writes naive queries | Core optimizes queries |
| **Permissions** | Hard to implement | Natural (HTTP middleware) |
| **Testing** | Must mock entire database | Mock HTTP calls (simpler) |
| **Caching** | Not possible | HTTP cache headers |
| **Rate Limiting** | Not possible | Trivial (middleware) |
| **Monitoring** | Difficult | API logs, metrics out of the box |

#### 3.3.5. Example: Complete Plugin Data Flow

```python
# FI/RE Calculator plugin example
from kanso_sdk import CoreAPI, PluginBase

class FireCalculatorPlugin(PluginBase):

    async def get_fire_dashboard(self):
        # 1. Fetch core data via API
        assets = await CoreAPI.get("/api/v1/assets", params={"type": "investment"})
        expenses = await CoreAPI.get("/api/v1/expenses", params={
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        })

        # 2. Read plugin-specific data from plugin DB
        with self.get_db_connection() as db:
            user_target = db.execute(
                "SELECT target_amount, target_date FROM fi_targets WHERE active = 1"
            ).fetchone()

        # 3. Calculate and return
        total_assets = sum(a["value"] for a in assets["data"])
        annual_expenses = sum(e["amount"] for e in expenses["data"])
        fire_number = annual_expenses * 25

        return {
            "current_assets": total_assets,
            "fire_number": fire_number,
            "progress": total_assets / fire_number * 100,
            "user_target": user_target["target_amount"] if user_target else None
        }
```

**Key Advantages**:
- ✅ Plugin never needs direct database credentials
- ✅ Core can change database schema without breaking plugins (API abstraction)
- ✅ Core can add caching, rate limiting, permissions at API layer
- ✅ Plugin testing is simpler (mock HTTP, not database)
- ✅ Security: Plugin cannot execute arbitrary SQL on core database

### 3.4. Frontend Integration

A **Micro-Frontend** architecture will be implemented using **Module Federation**.

*   **Plugin Discovery**: The main React app fetches a manifest from the backend listing all active plugins and their navigation entries (pages, titles, icons) to dynamically build the UI (e.g., a navigation drawer).
*   **Dynamic Loading**: The main app uses a "catch-all" route (`/plugins/:pluginId/*`) handled by a `PluginLoader` component. This component dynamically loads and renders the appropriate remote component from the plugin's own frontend build using Module Federation.
*   **Developer Freedom**: This approach gives plugin developers full freedom to build their UI with React, ensuring maximum flexibility while maintaining seamless integration.

### 3.5. Plugin Manifest Structure

Every plugin must include a `manifest.json` file at its root declaring its metadata, dependencies, and integration points. The manifest is validated before installation to ensure compatibility and security.

#### 3.5.1. Manifest Schema

```json
{
  "id": "fire-calculator",
  "version": "1.0.0",
  "name": "FI/RE Calculator",
  "description": "Calculate your path to Financial Independence and Early Retirement",
  "author": "Your Name",
  "repository": "https://github.com/yourname/kanso-plugin-fire",
  "license": "MIT",

  "type": "full-stack",

  "navigation": {
    "label": "FI/RE",
    "icon": "🔥",
    "routes": [
      {
        "path": "/plugins/fire-calculator/dashboard",
        "label": "Dashboard"
      },
      {
        "path": "/plugins/fire-calculator/scenarios",
        "label": "Scenarios"
      }
    ]
  },

  "backend": {
    "package": "kanso-plugin-fire",
    "module": "fire_plugin.router",
    "router": "plugin_router",
    "database": {
      "file": "plugin_fire.db",
      "schema": "backend/schema.sql"
    },
    "dependencies": {
      "kanso": ">=2.0.0,<3.0.0",
      "peers": {
        "fastapi": ">=0.104.0",
        "pandas": ">=2.1.0",
        "sqlalchemy": ">=2.0.0"
      }
    }
  },

  "frontend": {
    "entry": "remoteEntry.js",
    "peerDependencies": {
      "react": "^18.2.0",
      "react-dom": "^18.2.0",
      "react-router-dom": "^6.20.0"
    }
  },

  "permissions": {
    "read_core_tables": ["assets", "liabilities", "income", "expenses"]
  }
}
```

#### 3.5.2. Manifest Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | ✅ Yes | Unique plugin identifier (lowercase, hyphens only) |
| `version` | ✅ Yes | Semantic version (e.g., `1.0.0`) |
| `name` | ✅ Yes | Human-readable plugin name |
| `description` | ✅ Yes | Brief description of plugin functionality |
| `author` | ✅ Yes | Plugin author name or organization |
| `repository` | ✅ Yes | **Public GitHub repository URL** (security requirement) |
| `license` | ✅ Yes | Open source license (MIT, Apache 2.0, GPL, etc.) |
| `type` | ✅ Yes | `"full-stack"` or `"frontend-only"` |
| `navigation` | ✅ Yes | Navigation menu entries (label, icon, routes) |
| `backend` | Conditional | Required if `type` is `"full-stack"` |
| `backend.package` | ✅ Yes | Python package name (for `uv pip install`) |
| `backend.module` | ✅ Yes | Python module path containing the router |
| `backend.router` | ✅ Yes | Variable name of the FastAPI router object |
| `backend.database.file` | ✅ Yes | SQLite database filename for plugin |
| `backend.database.schema` | Conditional | SQL file to initialize database (simple plugins) |
| `backend.database.migrations` | Conditional | Alembic migrations directory (complex plugins) |
| `frontend` | ✅ Yes | Frontend configuration |
| `frontend.entry` | ✅ Yes | Module Federation entry point (relative to `frontend-dist/`) |
| `permissions` | ❌ No | Declarative permissions (currently informational) |

**Note on database initialization**:
- **Simple plugins** (recommended): Use `backend.database.schema` pointing to a SQL file. The core will execute this file once during installation.
- **Complex plugins**: Use `backend.database.migrations` pointing to an Alembic directory. The core will run `alembic upgrade head` during installation and updates.
- Only one of `schema` or `migrations` should be specified, not both.

#### 3.5.3. Manifest Validation

The Plugin Manager validates the manifest before any installation steps are executed:

1. **Structure Validation**: All required fields are present and correctly typed
2. **Dependency Compatibility**: Peer dependencies are compatible with the core application's versions
3. **Security Requirements**:
   - Repository must be a valid public GitHub URL
   - License must be an approved open source license
   - Plugin ID must not conflict with existing plugins
4. **Frontend Configuration**: Peer dependencies match Module Federation shared configuration

**Example validation error**:
```
❌ Plugin validation failed: fire-calculator

Issues found:
- backend.dependencies.peers.pandas: Plugin requires >=2.1.0, but core has 2.0.5
- repository: Must be a public GitHub URL (found: https://private-gitlab.com/...)
- license: License "Proprietary" is not open source

Installation aborted. No changes were made to your system.
```

### 3.6. Plugin SDK

The core provides official SDKs for both backend and frontend plugin development, abstracting common operations and providing utilities to accelerate plugin development.

#### 3.6.1. Backend SDK (`kanso-plugin-sdk`)

**Installation**:
```bash
uv pip install kanso-plugin-sdk
```

**Key Components**:

```python
from kanso_sdk import CoreAPI, PluginBase

class MyPlugin(PluginBase):
    """
    Base class providing utilities for plugin development.

    Automatically provides:
    - Core API client (self.core_api)
    - Database connection helpers (self.get_db_connection())
    - Plugin metadata (self.plugin_id, self.version)
    - Logging (self.logger)
    """

    async def get_data_from_core(self):
        # Access Core API with built-in authentication
        assets = await self.core_api.get("/api/v1/assets", params={
            "type": "investment",
            "min_value": 1000
        })
        return assets["data"]

    def store_calculation(self, result: dict):
        # Access plugin's own database
        with self.get_db_connection() as db:
            db.execute(
                "INSERT INTO calculations (result, created_at) VALUES (?, ?)",
                (json.dumps(result), datetime.now())
            )
            db.commit()
```

**CoreAPI Client**:

```python
from kanso_sdk import CoreAPI

# Automatic authentication using current user session
assets = await CoreAPI.get("/api/v1/assets")
expenses = await CoreAPI.get("/api/v1/expenses", params={
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "category": "food"
})

# Handles pagination automatically
all_transactions = await CoreAPI.get_all("/api/v1/expenses")  # Fetches all pages

# Error handling built-in
try:
    data = await CoreAPI.get("/api/v1/invalid")
except CoreAPIError as e:
    logger.error(f"Core API error: {e.status_code} - {e.message}")
```

**Testing Utilities**:

```python
from kanso_sdk.testing import MockCoreAPI
import pytest

@pytest.fixture
def mock_core():
    return MockCoreAPI(
        assets=[
            {"id": 1, "name": "Savings", "value": 10000, "type": "bank_account"},
            {"id": 2, "name": "Stocks", "value": 50000, "type": "investment"}
        ],
        expenses=[
            {"id": 1, "amount": 500, "category": "food", "date": "2024-11-01"}
        ]
    )

def test_plugin_calculation(mock_core):
    plugin = MyPlugin(core_api=mock_core)
    result = await plugin.calculate()
    assert result["total_assets"] == 60000
```

#### 3.6.2. Frontend SDK (`@kanso/plugin-sdk`)

**Installation**:
```bash
npm install @kanso/plugin-sdk
```

**Key Components**:

```typescript
import { useCoreAPI, KPICard, Chart, Table } from '@kanso/plugin-sdk'

export function PluginDashboard() {
  // React hook wrapping TanStack Query
  const { data: assets, isLoading, error } = useCoreAPI<Asset[]>({
    endpoint: '/api/v1/assets',
    params: { type: 'investment' }
  })

  if (isLoading) return <Loading />
  if (error) return <ErrorDisplay error={error} />

  const totalValue = assets.reduce((sum, a) => sum + a.value, 0)

  return (
    <>
      {/* Reusable components from core */}
      <KPICard
        title="Total Investments"
        value={totalValue}
        currency="EUR"
        trend={{ value: 5.2, direction: 'up' }}
      />

      <Chart
        type="pie"
        data={assets.map(a => ({ name: a.name, value: a.value }))}
        title="Asset Allocation"
      />

      <Table
        columns={[
          { key: 'name', label: 'Asset' },
          { key: 'value', label: 'Value', format: 'currency' }
        ]}
        data={assets}
        sortable
        paginated
      />
    </>
  )
}
```

**TypeScript Types**:

The SDK includes TypeScript definitions for all Core API responses:

```typescript
import type { Asset, Liability, Income, Expense } from '@kanso/plugin-sdk/types'

// Fully typed
const asset: Asset = {
  id: 1,
  name: "Savings Account",
  type: "bank_account",
  value: 10000,
  currency: "EUR",
  updated_at: "2024-11-06T10:00:00Z"
}
```

**Shared Components**:

The SDK exposes core UI components for consistent design:

- `<KPICard>`: Metric display with optional trend indicator
- `<Chart>`: ECharts wrapper with pre-configured themes
- `<Table>`: TanStack Table wrapper with sorting, filtering, pagination
- `<DateRangePicker>`: Consistent date selection
- `<CurrencyInput>`: Formatted currency input
- `<Button>`, `<Card>`, `<Dialog>`: shadcn/ui components

**Benefits of Using the SDK**:

| Without SDK | With SDK |
|-------------|----------|
| Manual HTTP fetch + auth | `useCoreAPI()` hook handles everything |
| Build UI components from scratch | Reuse core components (consistent UX) |
| Manual TypeScript types | Auto-generated types from OpenAPI |
| Custom error handling | Built-in error boundaries |
| Write mock server for tests | `MockCoreAPI` provided |

## 4. Plugin Lifecycle Management

A built-in **"Plugin Manager"** will handle the entire lifecycle of a plugin via the main application's UI.

### 4.1. Installation Process

The administrator installs a plugin by providing a URL to a GitHub release archive (e.g., `https://github.com/author/kanso-plugin-fire/releases/download/v1.0.0/kanso-plugin-fire-1.0.0.tar.gz`).

**Plugin Release Structure**:

Plugins are distributed as pre-built archives containing both backend source and **pre-compiled frontend assets**:

```
kanso-plugin-fire-1.0.0.tar.gz
├── manifest.json
├── backend/
│   ├── fire_plugin/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── models.py
│   ├── pyproject.toml
│   └── schema.sql
└── frontend-dist/              # ⭐ Pre-built, ready to serve
    ├── assets/
    │   ├── index-abc123.js
    │   └── index-def456.css
    ├── remoteEntry.js
    └── index.html
```

The Plugin Manager orchestrates the following automated steps:

1.  **Download & Validate**: Securely downloads the archive and validates its structure:
    - Checks for required files: `manifest.json`, `backend/pyproject.toml`, `frontend-dist/remoteEntry.js`
    - Validates manifest schema and compatibility (see section 3.5.3)
    - Ensures repository is public GitHub URL and license is open source
2.  **Install Backend**: Runs `uv pip install backend/` to install the plugin's Python package
3.  **Deploy Frontend**: Copies pre-built `frontend-dist/` to persistent location (e.g., `/var/www/plugins/fire/`) - **no build step required**
4.  **Configure Database**: Creates the plugin's dedicated SQLite database file (e.g., `data/plugin_fire.db`)
5.  **Initialize Schema**: Executes `backend/schema.sql` to create database tables (or runs Alembic migrations if specified)
6.  **Register Plugin**: Records the plugin in the core database's `plugin_installations` table with status `"active"`
7.  **Rollback on Failure**: If any step fails, all changes are automatically rolled back (see section 4.1.1)

**Key Advantage**: Frontend is pre-built by the plugin developer before release. This makes installation:
- ✅ **10x faster** (no `npm install` + `npm build` step)
- ✅ **More reliable** (zero npm/build failures during install)
- ✅ **Deterministic** (same artifact for all users)

#### 4.1.1. Error Handling & Automatic Rollback

The installation process is **atomic**: either all steps succeed, or everything is rolled back to the pre-installation state. Each step pushes a rollback action onto a stack. If an error occurs:

1. Installation stops immediately at the failed step
2. Rollback actions execute in reverse order:
   - Delete database file
   - Remove deployed frontend assets
   - Delete frontend build artifacts
   - Uninstall backend Python package
   - Remove downloaded plugin archive
3. User sees which step failed with detailed error logs
4. System returns to the exact pre-installation state

**Example installation flow with progress tracking**:

```
Installing plugin: FI/RE Calculator (v1.0.0)

✓ Downloaded archive (2s)
✓ Validated manifest and structure (1s)
✓ Validated dependencies (1s)
✓ Installed backend package (6s)
✓ Deployed frontend assets (2s)
✓ Created database and initialized schema (1s)
✓ Registered plugin (1s)

Installation complete! (14s total)

⚠️  Server restart required to activate plugin backend.

[Restart Now] [Restart Later]
```

**Example rollback on failure**:

```
Installing plugin: FI/RE Calculator (v1.0.0)

✓ Downloaded archive
✓ Validated manifest
✓ Validated dependencies
✗ Backend installation failed: Package 'numpy>=2.0' conflicts with core 'numpy==1.24.0'

Rolling back changes:
✓ Removed temporary files
✓ Cleaned up partially installed packages

Installation failed. Your system is unchanged.

Suggestion: Update your core application or contact the plugin author.

[View Full Logs] [Report Issue] [Cancel]
```

#### 4.1.2. Installation State Tracking

The core database tracks each plugin's installation state:

```sql
CREATE TABLE plugin_installations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plugin_id TEXT NOT NULL UNIQUE,
    version TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('installing', 'active', 'failed', 'disabled')),
    install_log TEXT,  -- JSON log of each installation step
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

This allows the UI to show:
- Currently installed plugins and their versions
- Installation history and logs
- Failed installation attempts with error details

### 4.2. Activation and Security

#### 4.2.1. Server Restart Requirement

After successful installation, the application must be restarted to load the new plugin's backend code. The UI prompts the administrator to trigger a graceful restart via a dedicated API endpoint:

```
✓ Plugin installed successfully: FI/RE Calculator (v1.0.0)

⚠️  Server restart required to activate plugin

The plugin's backend routes will be available after restart.
Frontend assets are already deployed and ready.

[Restart Now] [Restart Later]
```

This approach prioritizes **stability and simplicity** over hot-reloading, which would require complex dynamic import mechanisms and introduce potential runtime errors.

#### 4.2.2. Security Model

**Core Principle**: User responsibility with platform-enforced transparency.

The platform provides security through **database isolation** (section 3.3) and **manifest validation** (section 3.5.3), but ultimately **the user is responsible for trusting the plugin source**.

**Security Requirements Enforced by Platform**:

1. ✅ **Open Source Mandatory**: Plugin must link to public GitHub repository
2. ✅ **License Validation**: Only approved open source licenses (MIT, Apache 2.0, GPL, BSD)
3. ✅ **Database Isolation**: Plugins can only write to their own database file
4. ✅ **Dependency Validation**: Peer dependencies must be compatible with core

**Security Warning Shown Before Installation**:

```
⚠️  SECURITY WARNING

You are about to install a FULL-STACK plugin that will:
- Run Python code on your server with file system access
- Access all your financial data (read-only)
- Create and manage its own database

Plugin: FI/RE Calculator (v1.0.0)
Author: John Doe
Source: https://github.com/johndoe/kanso-plugin-fire
License: MIT

ONLY INSTALL PLUGINS FROM TRUSTED SOURCES

Actions you should take:
1. Review the source code on GitHub
2. Check the author's reputation
3. Verify the repository has recent activity
4. Look for community reviews/stars

[ ] I have reviewed the source code and trust this plugin
[ ] I understand this plugin will have access to my financial data

[Cancel] [Install Plugin]
```

**Attack Vectors and Mitigations**:

| Attack Vector | Platform Mitigation | User Responsibility |
|---------------|---------------------|---------------------|
| Malicious code execution | Database isolation prevents core corruption | Review source code before install |
| Data exfiltration | None - plugin can make network requests | Only install from trusted sources |
| Supply chain attack | Dependency validation catches version mismatches | Check plugin's dependencies in `pyproject.toml` |
| GitHub account compromise | None - relies on GitHub's security | Verify repository authenticity |

**Future Enhancements** (post-v2.0):

- 🔮 Code signing with GPG keys
- 🔮 Community star/rating system
- 🔮 Automated security scanning (static analysis)
- 🔮 Sandboxing with Docker-in-Docker or gVisor

### 4.3. Dependency Management

Plugins must declare compatibility with the core application and shared libraries to prevent version conflicts and runtime errors.

#### 4.3.1. Backend Dependencies

**Peer Dependencies Model**: The core defines minimum versions of shared libraries. Plugins must declare compatible versions.

**Core application** (`kanso-core/pyproject.toml`):

```toml
[project]
name = "kanso"
version = "2.0.0"
dependencies = [
    "fastapi>=0.104.0",
    "sqlalchemy>=2.0.0",
    "pandas>=2.1.0",
    "pydantic>=2.5.0",
]
```

**Plugin** (`kanso-plugin-fire/pyproject.toml`):

```toml
[project]
name = "kanso-plugin-fire"
version = "1.0.0"
dependencies = [
    "numpy>=1.24.0",      # Plugin-specific dependency
    "scipy>=1.11.0",      # Plugin-specific dependency
]

[tool.kanso.plugin]
requires_kanso = ">=2.0.0,<3.0.0"  # Semantic versioning
peer_dependencies = {
    fastapi = ">=0.104.0",
    pandas = ">=2.1.0",
    sqlalchemy = ">=2.0.0"
}
```

**Validation at install time**:

```python
# Plugin Manager validates before installation
def validate_backend_dependencies(manifest: dict) -> list[str]:
    errors = []
    core_deps = get_installed_versions()  # e.g., {"pandas": "2.1.4", "fastapi": "0.105.0"}
    plugin_peers = manifest["backend"]["dependencies"]["peers"]

    for dep, required_version in plugin_peers.items():
        installed_version = core_deps.get(dep)
        if not installed_version:
            errors.append(f"{dep}: Not installed in core")
        elif not is_version_compatible(installed_version, required_version):
            errors.append(
                f"{dep}: Plugin requires {required_version}, "
                f"but core has {installed_version}"
            )

    return errors
```

**Example error**:

```
❌ Dependency validation failed

Plugin "fire-calculator" requires:
- pandas>=2.1.0 (core has 2.0.5) ❌
- fastapi>=0.104.0 (core has 0.105.0) ✓
- sqlalchemy>=2.0.0 (core has 2.0.23) ✓

Please upgrade pandas in your core application:
  uv pip install --upgrade "pandas>=2.1.0"

Then try installing the plugin again.
```

#### 4.3.2. Frontend Dependencies

**Module Federation Shared Configuration**: Core and plugins must share the same major versions of React, React Router, and other critical libraries to prevent runtime errors.

**Core application** (`kanso-core/webpack.config.js`):

```javascript
const ModuleFederationPlugin = require('webpack/lib/container/ModuleFederationPlugin')
const path = require('path')

module.exports = {
  entry: './src/index',
  mode: 'production',
  output: {
    path: path.resolve(__dirname, 'dist'),
    publicPath: 'auto'
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx']
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/
      }
    ]
  },
  plugins: [
    new ModuleFederationPlugin({
      name: 'kansoCore',
      remotes: {},  // Populated dynamically at runtime
      exposes: {
        './KPICard': './src/components/KPICard',
        './Chart': './src/components/Chart',
        './Table': './src/components/Table'
      },
      shared: {
        react: {
          singleton: true,
          requiredVersion: '^18.2.0',
          strictVersion: true  // Fail if version mismatch
        },
        'react-dom': {
          singleton: true,
          requiredVersion: '^18.2.0',
          strictVersion: true
        },
        'react-router-dom': {
          singleton: true,
          requiredVersion: '^6.20.0',
          strictVersion: true
        }
      }
    })
  ]
}
```

**Plugin** (`kanso-plugin-fire/frontend/webpack.config.js`):

```javascript
const ModuleFederationPlugin = require('webpack/lib/container/ModuleFederationPlugin')
const path = require('path')

module.exports = {
  entry: './src/index',
  mode: 'production',
  output: {
    path: path.resolve(__dirname, 'dist'),
    publicPath: 'auto'
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx']
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader', 'postcss-loader']
      }
    ]
  },
  plugins: [
    new ModuleFederationPlugin({
      name: 'firePlugin',
      filename: 'remoteEntry.js',
      exposes: {
        './Dashboard': './src/pages/Dashboard',
        './Scenarios': './src/pages/Scenarios'
      },
      shared: {
        react: {
          singleton: true,
          requiredVersion: '^18.2.0'
        },
        'react-dom': {
          singleton: true,
          requiredVersion: '^18.2.0'
        },
        'react-router-dom': {
          singleton: true,
          requiredVersion: '^6.20.0'
        }
      }
    })
  ]
}
```

**Validation**: The Plugin Manager validates `manifest.json` frontend peer dependencies before building:

```json
// Plugin manifest.json
{
  "frontend": {
    "peerDependencies": {
      "react": "^18.2.0",
      "react-dom": "^18.2.0",
      "react-router-dom": "^6.20.0"
    }
  }
}
```

If a plugin declares incompatible versions (e.g., `"react": "^19.0.0"`), installation is rejected:

```
❌ Frontend dependency validation failed

Plugin "fire-calculator" requires React ^19.0.0
Core application uses React ^18.2.0

Module Federation requires singleton shared dependencies.
Please update your plugin to use React ^18.2.0.
```

#### 4.3.3. Dependency Update Strategy

**When core application updates shared dependencies**:

1. Update `pyproject.toml` and `package.json` with new versions
2. Document breaking changes in `CHANGELOG.md`
3. Bump core version following semantic versioning:
   - Patch (2.0.1): Bug fixes, no breaking changes
   - Minor (2.1.0): New features, backward compatible
   - Major (3.0.0): Breaking changes in shared dependencies

**Plugins declare version compatibility**:

```toml
[tool.kanso.plugin]
requires_kanso = ">=2.0.0,<3.0.0"  # Works with all 2.x versions
```

This ensures plugins continue working across minor/patch updates but must be explicitly updated for major version changes.

### 4.4. Plugin Release Process

Plugin developers create releases by building their plugin and packaging it for distribution via GitHub Releases.

#### 4.4.1. Build and Package Workflow

**Step 1: Build Frontend**

```bash
cd kanso-plugin-fire/frontend
npm install
npm run build  # Output: dist/
```

This generates production-optimized assets with Webpack Module Federation configuration.

**Step 2: Prepare Release Directory**

```bash
cd kanso-plugin-fire
mkdir -p release/backend
mkdir -p release/frontend-dist

# Copy backend source
cp -r backend/* release/backend/

# Copy pre-built frontend
cp -r frontend/dist/* release/frontend-dist/

# Copy manifest
cp manifest.json release/
```

**Step 3: Create Release Archive**

```bash
cd release
tar -czf ../kanso-plugin-fire-1.0.0.tar.gz .
cd ..
```

**Step 4: Publish to GitHub**

```bash
# Using GitHub CLI
gh release create v1.0.0 \
  --title "v1.0.0: Initial Release" \
  --notes "## Features
- 4% rule calculator
- FIRE target tracking
- Projection scenarios

## Installation
Install from Kanso Plugin Manager using:
https://github.com/yourname/kanso-plugin-fire/releases/download/v1.0.0/kanso-plugin-fire-1.0.0.tar.gz" \
  kanso-plugin-fire-1.0.0.tar.gz
```

**Step 5: Users Install**

Users install the plugin in Kanso's Plugin Manager UI by pasting the release URL:
```
https://github.com/yourname/kanso-plugin-fire/releases/download/v1.0.0/kanso-plugin-fire-1.0.0.tar.gz
```

#### 4.4.2. Release Checklist

Before publishing a release, plugin developers should:

- [ ] Update `manifest.json` version (semantic versioning)
- [ ] Update `backend/pyproject.toml` version to match manifest
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Run backend tests: `pytest backend/tests/`
- [ ] Run frontend tests: `npm test`
- [ ] Build frontend: `npm run build`
- [ ] Manually test plugin locally with development core
- [ ] Verify manifest peer dependencies are correct
- [ ] Create and test the release archive locally before publishing
- [ ] Write clear release notes explaining changes
- [ ] Tag release with semantic version (v1.0.0, v1.1.0, etc.)

#### 4.4.3. Semantic Versioning Strategy

Plugins should follow semantic versioning (MAJOR.MINOR.PATCH):

| Version Change | When to Use | Example |
|----------------|-------------|---------|
| **MAJOR** (1.0.0 → 2.0.0) | Breaking changes, incompatible with previous version | Changed Core API usage, removed routes, changed manifest structure |
| **MINOR** (1.0.0 → 1.1.0) | New features, backward compatible | Added new dashboard page, new calculation method, new settings |
| **PATCH** (1.0.0 → 1.0.1) | Bug fixes, no new features | Fixed calculation error, fixed UI bug, updated dependencies |

#### 4.4.4. Automated Release with GitHub Actions (Optional)

Plugin developers can automate the release process:

```yaml
# .github/workflows/release.yml
name: Release Plugin

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Build frontend
        run: |
          cd frontend
          npm install
          npm run build

      - name: Package plugin
        run: |
          mkdir -p release/backend release/frontend-dist
          cp -r backend/* release/backend/
          cp -r frontend/dist/* release/frontend-dist/
          cp manifest.json release/
          cd release
          tar -czf ../kanso-plugin-fire-${GITHUB_REF_NAME}.tar.gz .

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: kanso-plugin-fire-*.tar.gz
          generate_release_notes: true
```

With this setup, creating a release is as simple as:

```bash
git tag v1.0.0
git push origin v1.0.0
# GitHub Actions builds and publishes automatically
```

---

## 5. Core Features vs. Plugins

This section clarifies which features belong in the core application versus which should be implemented as plugins.

### 5.1. Core Application Scope

The **core application** provides the fundamental personal finance tracking features that define Kanso's value proposition:

#### Financial Data Management
- **Assets**: Track investment accounts, retirement accounts, savings, real estate
- **Liabilities**: Track loans, mortgages, credit cards, debts
- **Income**: Track salary, bonuses, passive income streams
- **Expenses**: Track monthly spending across categories

#### Core Visualizations
- **Net Worth Dashboard**: Primary KPI cards (net worth, income, expenses, savings ratio)
- **Trend Charts**: Net worth evolution over time, income vs. expenses
- **Breakdown Charts**: Expense categories, asset allocation

#### Data Sources
- **Google Sheets Integration**: Core feature allowing users to manage data in Google Sheets
  - Users choose at setup: **Google Sheets OR Local SQLite**
  - If Sheets selected: `core.db` becomes a cache with TTL refresh
  - Maintains API compatibility (v1.x feature)
- **Local SQLite**: Default zero-config option for self-hosted users
- **Manual Entry UI**: Forms for adding/editing financial data

#### Platform Features
- **Authentication & Authorization**: User accounts, sessions, API keys
- **Plugin Manager**: Discovery, installation, lifecycle management (section 4)
- **Settings & Configuration**: App preferences, data source configuration
- **Dark/Light Mode**: Theme system

### 5.2. Plugin Examples

Plugins extend the core application with specialized functionality:

#### Example 1: FI/RE Calculator (Official Plugin)
- **Purpose**: Calculate Financial Independence / Retire Early scenarios
- **Data**: Stores FI targets, withdrawal rates, projection scenarios in `plugin_fire.db`
- **Features**:
  - 4% rule calculator
  - Monte Carlo simulations for retirement scenarios
  - Coast FIRE, Lean FIRE, Fat FIRE calculators
- **UI**: New navigation entry "FI/RE" with Dashboard and Scenarios pages

#### Example 2: Stock Portfolio Tracker
- **Purpose**: Track individual stocks and portfolio performance
- **Data**: Stores stock prices, transactions, allocations in `plugin_stocks.db`
- **Features**:
  - Fetch real-time stock prices from external API
  - Calculate portfolio returns, dividends
  - Asset allocation visualization (pie chart by sector)
- **UI**: New navigation entry "Stocks" with Holdings and Performance pages

#### Example 3: Budget Tracker
- **Purpose**: Create and monitor monthly budgets
- **Data**: Stores budget limits, alerts in `plugin_budget.db`
- **Features**:
  - Set spending limits per category
  - Track budget vs. actual spending
  - Alert when approaching/exceeding limits
- **UI**: New navigation entry "Budgets" with Setup and Tracking pages

#### Example 4: Tax Optimization (Community Plugin)
- **Purpose**: Analyze tax implications and optimization strategies
- **Data**: Stores tax scenarios, deductions in `plugin_tax.db`
- **Features**:
  - Calculate tax liability based on income/expenses
  - Suggest tax-loss harvesting opportunities
  - Track deductible expenses
- **UI**: New navigation entry "Taxes" with Analysis and Reports pages

### 5.3. Decision Framework: Core vs. Plugin?

When deciding whether a feature belongs in core or as a plugin:

| Question | If YES → Core | If NO → Plugin |
|----------|---------------|----------------|
| Does it answer "Am I on track?" for ALL users? | ✅ | ❌ |
| Is it required for basic financial tracking? | ✅ | ❌ |
| Would 80%+ of users use this feature? | ✅ | ❌ |
| Does it involve managing core financial data (CRUD)? | ✅ | ❌ |
| Is it a specialized use case (FIRE, stocks, taxes)? | ❌ | ✅ |
| Does it integrate with external APIs/services? | ❌ | ✅ |
| Is it controversial or opinionated? | ❌ | ✅ |

**Examples**:
- ✅ **Core**: Net worth tracking (universal need)
- ❌ **Plugin**: FIRE calculator (specialized interest)
- ✅ **Core**: Expense categorization (fundamental)
- ❌ **Plugin**: Stock portfolio tracking (subset of users)
- ✅ **Core**: Google Sheets integration (differentiating feature)
- ❌ **Plugin**: Bank API sync (security concerns, optional)

---

## 6. Implementation Roadmap

This section outlines a suggested phased approach to building Kanso 2.0.

### Phase 1: Core Foundation (Milestone 2.0.0-alpha)
**Goal**: Working FastAPI + React app with core financial tracking, no plugins yet.

- [ ] FastAPI backend with SQLAlchemy + SQLite
- [ ] Core data models: Assets, Liabilities, Income, Expenses
- [ ] CRUD API endpoints for financial data
- [ ] React frontend with Vite
- [ ] Basic dashboard with KPI cards
- [ ] Google Sheets integration (read/write sync)
- [ ] Authentication & user management
- [ ] Docker Compose setup

**Estimated effort**: 6-8 weeks

### Phase 2: Plugin Architecture (Milestone 2.0.0-beta)
**Goal**: Plugin system working with one example plugin.

- [ ] Plugin manifest schema and validation
- [ ] Plugin Manager backend (install, rollback, state tracking)
- [ ] Plugin Manager UI (install from GitHub URL)
- [ ] Module Federation setup (core + remote loading)
- [ ] Dynamic navigation from plugin manifests
- [ ] Dependency validation (backend + frontend)
- [ ] Example plugin: "Hello World" (minimal full-stack plugin)

**Estimated effort**: 4-6 weeks

### Phase 3: First Real Plugin (Milestone 2.0.0-rc)
**Goal**: Ship FI/RE Calculator plugin to validate architecture.

- [ ] FI/RE plugin backend (calculations, API endpoints)
- [ ] FI/RE plugin frontend (Dashboard, Scenarios pages)
- [ ] Plugin database with Alembic migrations
- [ ] Cross-database queries (read core assets)
- [ ] Plugin documentation (README, API docs)
- [ ] Plugin template repository (for community developers)

**Estimated effort**: 3-4 weeks

### Phase 4: Stabilization (Milestone 2.0.0)
**Goal**: Production-ready v2.0 release.

- [ ] Comprehensive testing (unit + E2E)
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Documentation (user guide, plugin developer guide)
- [ ] Migration guide from v1.x (if applicable)
- [ ] Docker image optimization

**Estimated effort**: 2-3 weeks

**Total estimated effort**: ~15-21 weeks (4-5 months)

---

## 7. Conclusion

Kanso 2.0 represents a strategic architectural evolution focused on **extensibility through plugins** while maintaining the core philosophy of simplicity and data ownership.

### Key Architectural Decisions

1. **SQLite over PostgreSQL**: Simplicity and zero-config deployment outweigh the marginal benefits of PostgreSQL for personal finance workloads. Each plugin gets its own isolated database file.

2. **API-only data access**: Plugins access core data exclusively via HTTP API endpoints, never directly touching the core database. This provides security, versioning, and flexibility.

3. **Webpack 5 Module Federation**: Chosen over Vite for production-proven stability, excellent documentation, and mature dynamic remote loading support.

4. **Pre-built frontend in releases**: Plugin releases include pre-compiled frontend assets, making installation 10x faster and eliminating npm/build failures.

5. **Full-stack plugins by default**: Python + pandas on the backend enables powerful data analysis that would be impractical in browser-only JavaScript.

6. **manifest.json as single source of truth**: All plugin metadata, entry points, and dependencies declared in one validated file.

7. **Optional Alembic**: Simple plugins use `schema.sql` for database initialization. Alembic migrations only for complex plugins that evolve over time.

8. **React Context over Zustand**: Built-in React Context is sufficient for Kanso's simple global UI state (theme, preferences). TanStack Query handles all server state.

9. **User responsibility security model**: Platform enforces transparency (open source, manifest validation, database isolation) but trusts users to review code before installation.

10. **Peer dependency validation**: Strict version compatibility checks prevent "dependency hell" while allowing plugins to add their own libraries.

11. **Atomic installation with rollback**: Ensures system never ends up in inconsistent state after failed plugin install.

### Success Criteria

Kanso 2.0 will be considered successful if:

- ✅ Plugin developers can build and ship plugins **without modifying core**
- ✅ Users can install plugins via GitHub URL with **one click**
- ✅ Core application remains **simple to deploy** (docker-compose up)
- ✅ At least **3-5 community plugins** exist within 6 months of release
- ✅ No security incidents from plugin system in first year

### Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Low plugin adoption | High | High | Create 2-3 official plugins, excellent developer docs, template repo, plugin SDK |
| Security breach via malicious plugin | Medium | Critical | Clear warnings, code review culture, API-only data access, database isolation |
| Webpack build complexity | Low | Medium | Provide working webpack config in template, comprehensive docs |
| Version conflicts (deps hell) | Low | High | Strict peer dependency validation at install time, semantic versioning enforcement |
| API versioning breaking plugins | Low | High | Maintain v1 API compatibility, clear deprecation policy, semver core versions |
| Poor performance (SQLite limits) | Low | Medium | API caching, optimized aggregation endpoints, monitor query performance |
| Core API evolution | Medium | Medium | OpenAPI spec, versioned endpoints (/api/v1, /api/v2), backward compatibility commitment |

### Next Steps

1. **Review and approve** this architecture document
2. **Create GitHub repository** for Kanso 2.0 (separate from v1.x)
3. **Set up project structure** (monorepo with core + plugins?)
4. **Begin Phase 1 implementation** (FastAPI + React foundation)

This architecture provides a **solid foundation** for building a extensible, community-driven personal finance platform while learning from the proven patterns of v1.x and modern web application best practices.
