# Kanso – Your Minimal Money Tracker

![GitHub release (latest by date)](https://img.shields.io/github/v/release/dstmrk/kanso)
![CI](https://github.com/dstmrk/kanso/workflows/CI/badge.svg)
[![codecov](https://codecov.io/gh/dstmrk/kanso/branch/main/graph/badge.svg)](https://codecov.io/gh/dstmrk/kanso)
![GitHub](https://img.shields.io/github/license/dstmrk/kanso)

<table>
  <tr>
    <td><img src="docs/images/dashboard_light.png" alt="Light Mode"/></td>
    <td><img src="docs/images/dashboard_dark.png" alt="Dark Mode"/></td>
  </tr>
  <tr>
    <td align="center"><b>Light Mode</b></td>
    <td align="center"><b>Dark Mode</b></td>
  </tr>
</table>

**Kanso** is a minimalist, self-hostable web application designed to help you track your personal finances with clarity and calm. It leverages **Google Sheets** as the data source, and builds clean, interactive dashboards using **gspread**, **NiceGUI**, and **ECharts**.

---

## 📑 Table of Contents

- [Why "Kanso"?](#-why-kanso)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [First-Time Setup](#-first-time-setup)
- [Project Structure](#-project-structure)
- [Testing](#-testing)
- [Development](#️-development)
- [Tech Stack](#-tech-stack)
- [Documentation](#-documentation)
- [Security](#-security)
- [License](#-license)
- [Support](#-support)

---

## 🌱 Why "Kanso"?

> *Kanso (簡素)* is a Japanese word meaning **simplicity** and **elimination of the non-essential**.

This is not a tool for daily micro-management. It's for people who want to check in on their finances **once a month**, track big trends, and stay focused on what matters — without noise, stress, or overcomplication.

Your data stays in your Google Sheet. Kanso just makes it beautiful and easy to understand.

---

## ✨ Features

### Core Functionality
- 📊 **Interactive Dashboards** - Beautiful ECharts visualizations for income, expenses, and net worth
- 📈 **Trend Analysis** - Track financial trends over time with cumulative and monthly views
- 💰 **Multi-Currency Support** - EUR, USD, GBP, CHF, JPY with automatic formatting
- 🌓 **Dark/Light Mode** - Seamless theme switching with persistent preferences
- 📱 **Responsive Design** - Works beautifully on desktop, tablet, and mobile

### Data Management
- 📑 **Google Sheets Integration** - Your data stays in your own Google Sheet
- 🔄 **Real-time Updates** - Changes in your sheet reflect immediately
- ✅ **Data Validation** - Pydantic-based validation for data quality
- 💾 **Smart Caching** - Performance-optimized with intelligent cache invalidation
- 📊 **MultiIndex Support** - Handle complex sheet structures with ease

### User Experience
- 🚀 **Zero-Config Onboarding** - 3-step setup wizard for first-time users
- 🔐 **Secure Storage** - Credentials stored safely in encrypted browser storage
- ⚡ **Skeleton Loading** - Smooth loading experience with placeholders
- 🎯 **Settings Management** - Update credentials and preferences anytime
- 📉 **Expense Breakdown** - Detailed category analysis for spending insights

### Developer Experience
- 🧪 **Comprehensive Testing** - Full unit and E2E test suite with Playwright
- 🤖 **Smart CI/CD** - Intelligent E2E execution based on changed files
- 🐳 **Docker Ready** - Production-ready containerization
- 📝 **Type Safety** - Full mypy type checking
- 🎨 **Code Quality** - Automated linting with ruff and black

---

## 🚀 Quick Start

### Option 1: Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/dstmrk/kanso.git
cd kanso

# 2. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 3. Install dependencies
uv sync

# 4. Run the app
uv run main.py
```

Visit http://localhost:6789 and complete the onboarding setup!

### Option 2: Docker Deployment

See [DOCKER.md](./DOCKER.md) for complete Docker deployment instructions with docker-compose.

---

## 🎯 First-Time Setup

On your first visit, Kanso will guide you through a simple 3-step onboarding:

1. **Welcome** - Introduction to the setup process
2. **Credentials** - Paste your Google Service Account JSON credentials
   - Follow [this guide](https://docs.gspread.org/en/latest/oauth2.html#service-account) to create a service account
   - Copy and paste the JSON content into the provided textarea
3. **Configuration** - Enter your Google Sheet URL
   - Provide your spreadsheet URL (e.g., `https://docs.google.com/spreadsheets/d/...`)
   - Click "Save & Test Configuration" to validate

Your credentials are stored securely in your browser's encrypted storage.

After onboarding, your dashboard loads with skeleton placeholders while data is fetched from Google Sheets.

---

## 📂 Project Structure

```bash
kanso/
│
├── main.py                      # Application entry point
│
├── app/                         # Application code
│   ├── core/                   # Core utilities (config, validation, caching, monitoring)
│   ├── logic/                  # Business logic (financial calculations)
│   ├── services/               # External integrations (Google Sheets, data loading)
│   └── ui/                     # UI components (pages, charts, navigation)
│
├── tests/                       # Test suite
│   ├── unit/                   # Unit tests
│   ├── e2e/                    # Playwright end-to-end tests
│   └── conftest.py             # Test fixtures and configuration
│
├── docs/                        # Documentation and assets
├── .github/workflows/           # CI/CD pipelines
│
├── .env.{dev,prod,test}        # Environment configurations
├── Dockerfile                   # Container configuration
└── pyproject.toml              # Python dependencies and tooling
```

### Architecture

- **Separation of Concerns**: Clean separation between UI, business logic, and data access
- **Service Layer**: External integrations isolated in `services/`
- **State Management**: Centralized state with intelligent caching
- **Data Validation**: Non-blocking Pydantic validation for graceful error handling
- **Performance Monitoring**: Decorator-based tracking for data operations

---

## 🧪 Testing

Kanso has a comprehensive test suite covering both unit and end-to-end scenarios:

### Test Coverage

- **Unit Tests**: Covering core logic, services, and utilities
- **E2E Tests**: Playwright tests for complete user flows (onboarding, settings)
- **Coverage**: Focus on critical paths with automated coverage tracking

### Running Tests

```bash
# Run all unit tests
pytest -m "not e2e"

# Run E2E tests (requires Playwright browsers)
playwright install --with-deps chromium
pytest -m e2e --browser chromium

# Run all tests
pytest --browser chromium

# Run with coverage report
pytest -m "not e2e" --cov=app --cov-report=html
```

### CI/CD

The project uses a **smart CI strategy** that automatically runs E2E tests when UI files change:

- ✅ **Always**: Unit tests, linting, Docker build
- 🎯 **Smart**: E2E tests run on `main` push or when UI/service files change
- ⚡ **Fast**: ~2 min for most PRs, ~7 min when E2E tests run

See [.github/workflows/README.md](./.github/workflows/README.md) for details.

---

## 🛠️ Development

### Setup Development Environment

```bash
# Clone and install
git clone https://github.com/dstmrk/kanso.git
cd kanso
uv sync --all-extras  # Install dev dependencies

# Run in development mode
uv run main.py

# Run linters
uv run ruff check .
uv run black --check .
uv run mypy app --ignore-missing-imports

# Auto-format code
uv run black .
```

### Project Configuration

- **Package Manager**: [uv](https://docs.astral.sh/uv/) for fast, reliable dependency management
- **Linting**: [ruff](https://github.com/astral-sh/ruff) for fast Python linting
- **Formatting**: [black](https://github.com/psf/black) for consistent code style
- **Type Checking**: [mypy](https://mypy-lang.org/) for static type checking
- **Testing**: [pytest](https://pytest.org/) + [Playwright](https://playwright.dev/) for E2E

### Contributing

While this is primarily a personal project, contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests and linters pass
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

For E2E tests, include `[e2e]` in your commit message to trigger E2E CI runs.

---

## 🧩 Tech Stack

### Core Technologies
- **[Python 3.13](https://www.python.org/)** - Modern Python with latest performance improvements
- **[NiceGUI](https://nicegui.io)** - Pythonic web UI framework built on Vue/Quasar
- **[gspread](https://github.com/burnash/gspread)** - Google Sheets API wrapper
- **[pandas](https://pandas.pydata.org/)** - Data manipulation and analysis

### Frontend
- **[ECharts](https://echarts.apache.org/)** - Powerful data visualization library
- **[Tailwind CSS](https://tailwindcss.com/)** (via DaisyUI) - Utility-first CSS framework
- **[DaisyUI](https://daisyui.com/)** - Tailwind CSS component library

### Development & Testing
- **[pytest](https://pytest.org/)** - Python testing framework
- **[Playwright](https://playwright.dev/)** - Browser automation for E2E tests
- **[Pydantic](https://pydantic.dev/)** - Data validation using Python type hints
- **[mypy](https://mypy-lang.org/)** - Static type checker
- **[ruff](https://github.com/astral-sh/ruff)** - Fast Python linter
- **[black](https://github.com/psf/black)** - Opinionated code formatter

### DevOps
- **[Docker](https://www.docker.com/)** - Containerization
- **[GitHub Actions](https://github.com/features/actions)** - CI/CD automation
- **[uv](https://docs.astral.sh/uv/)** - Fast Python package manager

---

## 📚 Documentation

- **[Docker Deployment Guide](./DOCKER.md)** - Production deployment with Docker
- **[CI/CD Workflow Guide](./.github/workflows/README.md)** - GitHub Actions workflow documentation
- **[Security Policy](./SECURITY.md)** - Security guidelines and vulnerability reporting

---

## 🔒 Security

Security is a priority. Please review our [Security Policy](./SECURITY.md) for:
- Supported versions
- Vulnerability reporting process
- Security best practices

**Never commit credentials or secrets.** Kanso stores credentials securely in encrypted browser storage.

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](./LICENSE) file for details.

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/dstmrk/kanso/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dstmrk/kanso/discussions)
- **Security**: See [SECURITY.md](./SECURITY.md)

---

<p align="center">
  Made with ❤️ and a focus on simplicity
</p>
