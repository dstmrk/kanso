# Kanso – Your Minimal Money Tracker

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

### 6. Create a .env file

In the project root, create a .env file with the following keys:

```bash
GOOGLE_SHEET_CREDENTIALS_FILENAME=the_filename_of_your_Google_Sheet_API_credentials
WORKBOOK_URL=your_google_sheet_workbook_url
```

Replace values as appropriate. The ECharts theme can be customized using the [ECharts Theme Builder](https://echarts.apache.org/en/theme-builder.html)

### 7. Run the app

Visit http://localhost:6789 to access your dashboard. You can customize the port by using the PORT key in the .env file

## 📂 Structure

```bash
kanso/
│
├── main.py               # Entry point of the app
├── requirements.txt      # Python dependencies
├── .env                  # Environment config
├── config/credentials    # Google API credentials folder
└── ...
```

## 🧩 Tech Stack

- [gspread](https://github.com/burnash/gspread) – Google Sheets API wrapper
- [NiceGUI](https://nicegui.io) – UI framework for Python Web App
- [ECharts](https://echarts.apache.org/en/index.html) – Data visualizations library
