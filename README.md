# Kanso – Your Minimal Money Tracker

![GitHub release (latest by date)](https://img.shields.io/github/v/release/marcodestefano/kanso?cache=0)
![GitHub](https://img.shields.io/github/license/marcodestefano/kanso?cache=0)
![Python Version](https://img.shields.io/badge/python-3.13-blue)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen)

**Kanso** is a minimalist, self-hostable web application designed to help you track your personal finances with clarity and calm. It leverages **Google Sheets** as the data source, and builds clean, interactive dashboards using **gspread**, **NiceGUI**, and **ECharts**.

---

## 🌱 Why "Kanso"?

> *Kanso (簡素)* is a Japanese word meaning **simplicity**, **plainness**, or **elimination of the non-essential**.
> It comes from traditional Japanese aesthetics, emphasizing clarity, intentionality, and calm.
> This tool was built with that spirit in mind: a minimalist finance tracker that doesn't overwhelm you.

---

## 🧘 Philosophy

This is not a tool for micro-managing finances daily.

It's for people who want to check in on their finances once a month, track big trends, and stay focused on what matters — without noise, stress, or overcomplication.

---

## ⚙️ What It Does

- Reads data from a Google Sheets workbook
- Builds monthly and cumulative dashboards for income, expenses, and savings
- Lets you update your data **just once a month**
- Provides a minimalist, low-friction interface via **NiceGUI**
- Uses **ECharts** for beautiful, responsive charts

---

## 🚀 How to Run It

### 1. Clone the repository

```bash
git clone https://github.com/marcodestefano/kanso.git
cd kanso
```

### 2. Install [uv](https://docs.astral.sh/uv/) as python package and environment manager
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh # On Windows Powershell: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

or
```bash
pip install uv
```

### 3. Set up a virtual environment
```bash
uv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install requirements
```bash
uv sync
```

### 5. Set up Google Sheets API credentials

- Follow the official guide to create a service account and download the JSON file:
👉 https://docs.gspread.org/en/latest/oauth2.html#service-account
- Save the credentials JSON file in config/credentials folder.

### 6. Configure your environment

Edit `.env.dev.local` with your personal data:

```bash
GOOGLE_SHEET_CREDENTIALS_FILENAME=your_google_sheet_credentials_filename
WORKBOOK_URL=the_workbook_url_of_your_google_sheet_file
ROOT_PATH=  # Leave empty unless using a reverse proxy
```

> **Note**: `.env.dev.local` is gitignored for security. The app auto-loads `.env.dev` + `.env.dev.local` when you run it.

### 7. Run the app

```bash
uv run main.py
```

Visit http://localhost:6789 to access your dashboard.

**For Docker deployment**, see [DOCKER.md](./DOCKER.md) for complete instructions.

## 📂 Structure

```bash
kanso/
│
├── main.py                  # Entry point
├── app/                     # Application code
│   ├── core/               # Core config & constants
│   ├── logic/              # Business logic
│   ├── services/           # External services (Google Sheets)
│   └── ui/                 # UI components
├── config/credentials/      # Google API credentials (gitignored)
├── .env.dev                 # Dev config template (committed)
├── .env.dev.local          # Your dev overrides (gitignored)
├── .env.prod               # Prod config template (committed)
├── .env.prod.local         # Your prod overrides (gitignored)
├── Dockerfile              # Docker build config
├── docker-compose.yaml     # Docker orchestration
└── DOCKER.md               # Docker deployment guide
```

## 🧩 Tech Stack

- [gspread](https://github.com/burnash/gspread) – Google Sheets API wrapper
- [NiceGUI](https://nicegui.io) – UI framework for Python Web App
- [ECharts](https://echarts.apache.org/en/index.html) – Data visualizations library
