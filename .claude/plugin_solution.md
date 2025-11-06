# Project Architecture & Technology Stack: A Comprehensive Overview

## 1. Vision

The goal is to build a modern, open-source (MIT license) data analysis and visualization application. The platform's cornerstone feature is its extensibility, allowing a community of third-party developers to create and distribute "plugins" that seamlessly integrate with the main application. The architecture is designed to be robust, scalable, and maintainable, prioritizing a clean separation of concerns, a high-quality codebase, and a superior developer experience.

## 2. Core Technology Stack

This stack is a curated collection of mature, best-in-class tools covering the entire development lifecycle, from coding and testing to deployment.

| Category                | Technology                                         | Rationale                                                                      |
| :---------------------- | :------------------------------------------------- | :----------------------------------------------------------------------------- |
| **Backend Framework**   | **FastAPI** (with `uv` for package management)     | High-performance, modern, async-native, with automatic API documentation.      |
| **Database & ORM**      | **SQLite** + **SQLAlchemy** + **Alembic**          | Simple, zero-config persistence with multi-database support for plugin isolation. Lightweight and perfect for self-hosted personal finance applications. |
| **Backend Testing**     | **Pytest** + **HTTPX**                             | The de-facto standard for writing clean, scalable tests for Python applications. |
| **Backend Code Quality**| **Ruff**                                           | An all-in-one, high-speed linter and formatter for maintaining a clean Python codebase. |
| **Frontend Framework**  | **React** (bootstrapped with **Vite**)             | The industry standard for data-intensive applications with a vast ecosystem.       |
| **Frontend Routing**    | **React Router**                                   | The standard library for client-side routing in React applications.              |
| **Server State Mgmt**   | **TanStack Query**                                 | Crucial for fetching, caching, and syncing server data. Reduces boilerplate and improves UX. |
| **Client State Mgmt**   | **Zustand**                                        | A minimal, modern solution for global UI state that isn't tied to the server. |
| **UI Components**       | **shadcn/ui** + **Tailwind CSS**                   | A modern, accessible, and themeable component system for rapid UI development. |
| **Data Visualization**  | **TanStack Table v8** + **Apache ECharts**         | Best-in-class libraries for building powerful, interactive tables and charts.  |
| **Frontend Testing**    | **Vitest** + **React Testing Library**             | The modern, fast standard for testing React applications built with Vite.          |
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

### 3.3. Database Integration

A multi-database model using SQLite provides strong isolation while maintaining simplicity and zero-config deployment.

*   **Dedicated Database File**: Upon installation, a dedicated SQLite database file is created for each plugin in the data directory (e.g., `data/plugin_fire.db`, `data/plugin_stocks.db`).
*   **Isolated Write Access**: Each plugin writes exclusively to its own database file using SQLAlchemy with a dedicated connection string. Plugins have full control over their schema and can use **Alembic** for migrations without affecting the core application.
*   **Global Read-Only Access**: Plugins can read core data by attaching the core database and performing cross-database queries using SQLite's `ATTACH DATABASE` feature.

#### 3.3.1. Database Structure

```
/data/
  ├── core.db              # Core Kanso database (assets, liabilities, income, expenses)
  ├── plugin_fire.db       # FIRE Calculator plugin data (fi_targets, withdrawal_scenarios)
  ├── plugin_stocks.db     # Stocks plugin data (stock_prices, portfolio_allocations)
  └── plugin_budget.db     # Budget Tracker plugin data (budgets, alerts)
```

#### 3.3.2. Cross-Database Queries

Plugins can query core data alongside their own tables using SQLite's `ATTACH DATABASE` feature:

```python
# Example: Plugin querying core assets + plugin-specific data
from sqlalchemy import create_engine, text

# Plugin's own database connection
plugin_engine = create_engine('sqlite:///data/plugin_fire.db')

with plugin_engine.connect() as conn:
    # Attach core database for read access
    conn.execute(text("ATTACH DATABASE 'data/core.db' AS core"))

    # Cross-database query joining core and plugin tables
    result = conn.execute(text("""
        SELECT
            a.id,
            a.name,
            a.value,
            a.type,
            f.fire_target,
            f.withdrawal_rate
        FROM core.assets a
        LEFT JOIN fi_targets f ON a.id = f.asset_id
        WHERE a.type IN ('investment', 'retirement')
        ORDER BY a.value DESC
    """))

    for row in result:
        print(f"{row.name}: ${row.value} (FI Target: ${row.fire_target})")
```

**Key Benefits**:
- ✅ Plugins can read all core financial data (assets, liabilities, income, expenses)
- ✅ Plugins maintain their own schema independently
- ✅ Zero risk of plugins corrupting core data (write isolation)
- ✅ Simple backup: copy individual `.db` files

**Limitations**:
- ⚠️ SQLite does not support transactions across attached databases
- ⚠️ Plugins should read from core and write to their own DB in separate transactions
- ⚠️ Concurrent writes are serialized (database-level lock), but this is not an issue for personal finance workloads

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
    "entry_point": "fire_plugin.main:plugin_router",
    "database": {
      "file": "plugin_fire.db",
      "migrations": "alembic/"
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
    "entry": "dist/remoteEntry.js",
    "build_command": "npm run build",
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
| `frontend` | ✅ Yes | Frontend build configuration |
| `permissions` | ❌ No | Declarative permissions (currently informational) |

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

## 4. Plugin Lifecycle Management

A built-in **"Plugin Manager"** will handle the entire lifecycle of a plugin via the main application's UI.

### 4.1. Installation Process

The administrator installs a plugin by providing a URL to a GitHub release archive (e.g., `https://github.com/author/kanso-plugin-fire/releases/download/v1.0.0/plugin.tar.gz`). The Plugin Manager orchestrates the following automated steps:

1.  **Download & Validate**: Securely downloads the archive and validates its structure against the "Plugin Contract":
    - Checks for required files: `manifest.json`, `pyproject.toml`, `vite.config.js`
    - Validates manifest schema and compatibility (see section 3.5.3)
    - Ensures repository is public GitHub URL and license is open source
2.  **Install Backend**: Runs `uv pip install` to install the plugin's Python package into the main application's environment
3.  **Build Frontend**: Runs `npm install` and `npm run build` within the plugin's frontend directory to generate static assets
4.  **Deploy Frontend**: Moves the built static assets to a persistent, publicly served location (e.g., `/var/www/plugins/fire/`)
5.  **Configure Database**: Creates the plugin's dedicated SQLite database file (e.g., `data/plugin_fire.db`)
6.  **Run Migrations**: If the plugin includes Alembic migrations, runs `alembic upgrade head` to create the plugin's schema
7.  **Register Plugin**: Records the plugin in the core database's `plugin_installations` table with status `"active"`
8.  **Rollback on Failure**: If any step fails, all changes are automatically rolled back (see section 4.1.1)

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

✓ Downloaded and validated manifest (2s)
✓ Validated dependencies (1s)
✓ Installed backend package (8s)
⏳ Building frontend... (45s elapsed)
   Running: npm install && npm run build
   [████████████████░░░░] 80% - Optimizing bundle...
```

**Example rollback on failure**:

```
Installing plugin: FI/RE Calculator (v1.0.0)

✓ Downloaded and validated manifest
✓ Validated dependencies
✓ Installed backend package
✗ Build failed: npm build exited with code 1

Error details:
  Module not found: Can't resolve 'invalid-package'
  at frontend/src/Dashboard.tsx:3

Rolling back changes:
✓ Removed frontend build artifacts
✓ Uninstalled backend package (kanso-plugin-fire)
✓ Cleaned up temporary files

Installation failed. Your system is unchanged.

[View Full Logs] [Report Issue] [Try Again]
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

**Core application** (`kanso-core/vite.config.js`):

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import federation from '@originjs/vite-plugin-federation'

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'kansoCore',
      remotes: {},  // Populated dynamically with plugin URLs
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
          requiredVersion: '^6.20.0'
        }
      }
    })
  ]
})
```

**Plugin** (`kanso-plugin-fire/vite.config.js`):

```javascript
export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'firePlugin',
      filename: 'remoteEntry.js',
      exposes: {
        './Dashboard': './src/Dashboard.tsx',
        './Scenarios': './src/Scenarios.tsx'
      },
      shared: {
        react: { singleton: true, requiredVersion: '^18.2.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.2.0' },
        'react-router-dom': { singleton: true, requiredVersion: '^6.20.0' }
      }
    })
  ]
})
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

1. **SQLite over PostgreSQL**: Simplicity and zero-config deployment outweigh the marginal benefits of PostgreSQL for personal finance workloads
2. **Full-stack plugins by default**: Python + pandas on the backend enables powerful data analysis that would be impractical in browser-only JavaScript
3. **Module Federation**: Industry-standard micro-frontend approach provides true plugin isolation and independent deployment
4. **User responsibility security model**: Platform enforces transparency (open source, manifest validation, database isolation) but trusts users to review code
5. **Peer dependency validation**: Prevents version conflicts while allowing plugins to use additional libraries
6. **Atomic installation with rollback**: Ensures system never ends up in inconsistent state after failed plugin install

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
| Low plugin adoption | High | High | Create 2-3 official plugins, excellent developer docs, template repo |
| Security breach via malicious plugin | Medium | Critical | Clear warnings, code review culture, database isolation |
| Module Federation complexity | Medium | Medium | Invest in plugin template, thorough documentation |
| Version conflicts (deps hell) | Medium | High | Strict peer dependency validation, semantic versioning |
| Poor performance (SQLite limits) | Low | Medium | Monitor, migrate to PostgreSQL only if needed |

### Next Steps

1. **Review and approve** this architecture document
2. **Create GitHub repository** for Kanso 2.0 (separate from v1.x)
3. **Set up project structure** (monorepo with core + plugins?)
4. **Begin Phase 1 implementation** (FastAPI + React foundation)

This architecture provides a **solid foundation** for building a extensible, community-driven personal finance platform while learning from the proven patterns of v1.x and modern web application best practices.
