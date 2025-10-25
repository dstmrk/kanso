# Installation Guide

This guide walks you through installing and running Kanso using Docker (recommended) or local development setup.

## Prerequisites

=== "Docker (Recommended)"

    - **Docker** and **Docker Compose**
    - Modern web browser (Chrome, Firefox, Safari, Edge)

=== "Local Development"

    - **Python** 3.13+
    - **uv** package manager ([install guide](https://github.com/astral-sh/uv))
    - Modern web browser

## Quick Start with Docker

**No repository clone needed!** Use the pre-built Docker image.

### Step 1: Download Docker Compose File

```bash
# Create a directory for Kanso
mkdir kanso && cd kanso

# Download the production compose file
curl -o docker-compose.yml https://raw.githubusercontent.com/dstmrk/kanso/main/docker-compose.yml
```

Or create `docker-compose.yml` manually:

```yaml
services:
  kanso:
    image: ghcr.io/dstmrk/kanso:latest
    ports:
      - "6789:6789"
    environment:
      - APP_ENV=prod
      - LOG_LEVEL=WARNING
    volumes:
      - ./kanso-data:/app/data
    restart: unless-stopped
```

### Step 2: Start Kanso

```bash
docker compose up -d
```

This will:

1. Pull the latest Kanso Docker image
2. Start the application on port 6789
3. Create a persistent volume for data storage

### Step 3: Access the Application

Open your browser and navigate to:

```
http://localhost:6789
```

You'll see the onboarding wizard on first launch.

### Optional Configuration

To customize settings, edit the `docker-compose.yml` environment section:

```yaml
environment:
  - APP_ENV=prod              # Environment (dev/prod)
  - LOG_LEVEL=WARNING         # Log level (DEBUG, INFO, WARNING, ERROR)
  - APP_PORT=6789             # Application port
  - CACHE_TTL_SECONDS=86400   # Cache duration (24 hours)
  - ROOT_PATH=                # Reverse proxy path
```

## Local Development Setup

### Step 1: Install Dependencies

```bash
# Clone repository
git clone https://github.com/dstmrk/kanso.git
cd kanso

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

### Step 2: Run the Application

```bash
uv run python main.py
```

The application will start on `http://localhost:6789`.

!!! tip "Development Environment"
    For development, use `.env.dev` which enables debug mode and hot-reload:
    ```bash
    ln -s .env.dev .env
    ```

### Step 3: Run Tests (Optional)

```bash
# Run unit tests
uv run pytest tests/unit/ -v

# Run E2E tests (requires Playwright)
uv run playwright install chromium
uv run pytest tests/e2e/ -v
```

## First-Time Setup

When you first access Kanso, you'll see the **onboarding wizard**:

1. **Welcome Screen** - Introduction to Kanso
2. **Storage Setup** - Configure Google Sheets credentials (service account JSON and sheet URL)

After completing onboarding, you'll be redirected to the dashboard.

!!! warning "Google Sheets Required (v0.3.0)"
    Current version requires Google Sheets as data backend. SQLite local storage is coming in v0.8.0.

## Next Steps

- **[Google Sheets Setup](google-sheets-setup.md)** - Prepare your financial data
- **[Configuration Guide](configuration.md)** - Customize Kanso settings
- **[Architecture Overview](architecture.md)** - Understand how Kanso works

## Troubleshooting

### Port Already in Use

If port 6789 is already taken, change it in `.env`:

```bash
APP_PORT=8080
```

And update your `docker-compose.yml` accordingly.

### Docker Compose Issues

Check logs for errors:

```bash
docker compose logs -f kanso
```

Rebuild the image:

```bash
docker compose build --no-cache
docker compose up -d
```

### Permission Errors

Ensure the data directory is writable:

```bash
mkdir -p ./kanso-data
chmod 755 ./kanso-data
```

### Browser Storage Issues

Clear browser storage and cookies for `localhost:6789` if you see authentication issues.

## Updating Kanso

### Docker Compose

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Local Development

```bash
# Pull latest changes
git pull origin main

# Update dependencies
uv sync

# Restart application
uv run python main.py
```

## Uninstalling

### Docker

```bash
# Stop and remove containers
docker compose down

# Remove volumes (⚠️ deletes all data)
docker compose down -v

# Remove images
docker rmi kanso:latest
```

### Local Development

```bash
# Remove virtual environment
rm -rf .venv

# Remove data directory
rm -rf ./kanso-data
```

!!! danger "Data Backup"
    Before uninstalling, export your data from Google Sheets or backup the `kanso-data` directory.
