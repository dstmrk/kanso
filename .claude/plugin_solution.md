# Project Architecture & Technology Stack: A Comprehensive Overview

## 1. Vision

The goal is to build a modern, open-source (MIT license) data analysis and visualization application. The platform's cornerstone feature is its extensibility, allowing a community of third-party developers to create and distribute "plugins" that seamlessly integrate with the main application. The architecture is designed to be robust, scalable, and maintainable, prioritizing a clean separation of concerns, a high-quality codebase, and a superior developer experience.

## 2. Core Technology Stack

This stack is a curated collection of mature, best-in-class tools covering the entire development lifecycle, from coding and testing to deployment.

| Category                | Technology                                         | Rationale                                                                      |
| :---------------------- | :------------------------------------------------- | :----------------------------------------------------------------------------- |
| **Backend Framework**   | **FastAPI** (with `uv` for package management)     | High-performance, modern, async-native, with automatic API documentation.      |
| **Database & ORM**      | **PostgreSQL** + **SQLAlchemy** + **Alembic**      | The gold standard for robust data persistence and version-controlled schema management. |
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

A hybrid model is used to ensure both flexibility and security.

*   **Dedicated Schema**: Upon installation, a dedicated PostgreSQL schema is created for each plugin (e.g., `CREATE SCHEMA plugin_id;`).
*   **Isolated Write Access**: A dedicated database role is created for the plugin, granted `ALL PRIVILEGES` on its own schema. This allows the plugin to use **SQLAlchemy** and **Alembic** to manage its own tables without affecting the core application.
*   **Global Read-Only Access**: The same role is granted `SELECT` privileges on the main application's `public` schema, allowing plugins to read core data for context.

### 3.4. Frontend Integration

A **Micro-Frontend** architecture will be implemented using **Module Federation**.

*   **Plugin Discovery**: The main React app fetches a manifest from the backend listing all active plugins and their navigation entries (pages, titles, icons) to dynamically build the UI (e.g., a navigation drawer).
*   **Dynamic Loading**: The main app uses a "catch-all" route (`/plugins/:pluginId/*`) handled by a `PluginLoader` component. This component dynamically loads and renders the appropriate remote component from the plugin's own frontend build using Module Federation.
*   **Developer Freedom**: This approach gives plugin developers full freedom to build their UI with React, ensuring maximum flexibility while maintaining seamless integration.

## 4. Plugin Lifecycle Management

A built-in **"Plugin Manager"** will handle the entire lifecycle of a plugin via the main application's UI.

### 4.1. Installation Process

The administrator installs a plugin by providing a URL to a GitHub release archive. The Plugin Manager then orchestrates the following automated steps:

1.  **Download & Validate**: Securely downloads the archive and validates its structure against the "Plugin Contract" (checking for `pyproject.toml`, `vite.config.js`, `alembic/` directory, etc.).
2.  **Install Backend**: Runs `uv pip install` to install the plugin's Python package into the main application's environment.
3.  **Build Frontend**: Runs `npm install` and `npm run build` within the plugin's frontend directory to generate its static assets.
4.  **Deploy Frontend**: Moves the built static assets to a persistent, publicly served location.
5.  **Configure Database**: Creates the dedicated schema and role in PostgreSQL.
6.  **Run Migrations**: Invokes the plugin's **Alembic** command to apply its database migrations to its newly created schema.
7.  **Activate**: Marks the plugin as successfully installed in the database.

### 4.2. Activation and Security

*   **Server Restart Required**: After installation, the application must be restarted to load the new plugin. The UI will prompt the admin to do this via a dedicated API endpoint that triggers a graceful restart of the Docker service. This choice prioritizes stability and simplicity.
*   **Shared Responsibility Security Model**: The platform provides security through strong isolation. However, the admin is ultimately responsible for trusting the source of the plugin. The UI will display a clear warning before installing third-party code, promoting the inspection of the open-source repository.
