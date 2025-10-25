# Welcome to Kanso

**Kanso** is a self-hosted personal finance tracker designed for calm, monthly check-ins with your financial data. Track your net worth, expenses, income, and savings with clarity—no anxiety, no subscription fees, no vendor lock-in.

<div class="grid cards" markdown>

- :material-chart-line: **Clear Insights**

    ---

    Interactive dashboards with net worth tracking, cash flow analysis, and expense breakdowns. Understand your finances at a glance.

- :material-shield-lock: **Your Data, Your Control**

    ---

    Self-hosted with Docker. Your financial data never leaves your infrastructure. Works with Google Sheets or local storage (coming in v0.8.0).

- :material-lightning-bolt: **Zero-Config Start**

    ---

    Get started in minutes with Docker Compose. Built-in onboarding wizard guides you through setup.

- :material-atom: **Calm Technology**

    ---

    Designed for monthly check-ins, not daily anxiety. Focus on insights, not notification spam.

</div>

## Features

### 📊 Financial Tracking
- **Net worth** evolution with assets and liabilities
- **Cash flow** analysis with income and expenses
- **Category breakdowns** for spending patterns
- **Savings ratio** tracking over time
- **Multi-currency support** (EUR, USD, GBP, CHF, JPY)

### 🎨 Modern UI
- **Interactive charts** built with ECharts
- **Responsive design** works on mobile and desktop
- **Light/dark mode** toggle
- **Transaction tables** with search and filtering

### 🔧 Technical Excellence
- **Self-hosted** with Docker - full control of your data
- **Google Sheets backend** - edit data anywhere, sync automatically
- **Python + NiceGUI** - modern async architecture
- **Comprehensive testing** - extensive unit and E2E test coverage
- **Type-safe** with mypy validation

## Quick Start

=== "Docker (Recommended)"

    ```bash
    # Create directory and download compose file
    mkdir kanso && cd kanso
    curl -o docker-compose.yml https://raw.githubusercontent.com/dstmrk/kanso/main/docker-compose.yml

    # Start Kanso
    docker compose up -d

    # Open http://localhost:6789
    ```

=== "Local Development"

    ```bash
    # Clone and install dependencies
    git clone https://github.com/dstmrk/kanso.git
    cd kanso
    uv sync

    # Run the application
    uv run python main.py

    # Open http://localhost:6789
    ```

## Philosophy

Kanso embraces **calm technology** principles:

1. **Simplicity First** - Features serve monthly check-ins, not feature bloat
2. **Your Data, Your Control** - Self-hosted, exportable, no lock-in
3. **Privacy by Design** - No tracking, no telemetry, only Google Sheets API for data access
4. **Progressive Complexity** - Start simple, add complexity when needed

## What's Next?

<div class="grid cards" markdown>

- :material-download: [**Installation Guide**](installation.md)

    ---

    Set up Kanso with Docker, configure Google Sheets, and get your first dashboard running.

- :material-table: [**Google Sheets Setup**](google-sheets-setup.md)

    ---

    Learn how to structure your financial data in Google Sheets for Kanso.

- :material-cog: [**Configuration**](configuration.md)

    ---

    Customize themes, currency, and environment variables.

- :material-code-tags: [**Architecture**](architecture.md)

    ---

    Understand Kanso's technical design and how components work together.

</div>

## Community & Support

- **GitHub Issues** - [Report bugs or request features](https://github.com/dstmrk/kanso/issues)
- **Discussions** - [Ask questions and share ideas](https://github.com/dstmrk/kanso/discussions)
- **Contributing** - [Learn how to contribute](contributing.md)

## License

Kanso is open source software licensed under [MIT License](https://github.com/dstmrk/kanso/blob/main/LICENSE).
