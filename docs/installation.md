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
      - "9525:9525"  # Change host port if needed (e.g., "8080:9525")
    environment:
      - APP_ENV=prod
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
2. Start the application on port 9525
3. Create a persistent volume for data storage

### Step 3: Access the Application

Open your browser and navigate to:

```
http://localhost:9525
```

You'll see the onboarding wizard on first launch.

!!! tip "Before Starting the Wizard"
    Make sure you have ready:

    - **Google Sheets service account JSON** - See [Google Sheets Setup](google-sheets-setup.md)
    - **Your Google Sheet URL** - The spreadsheet where your financial data is stored

    Having these ready ensures a smooth onboarding experience!

### Optional Configuration

The application uses default settings from `.env.prod` (embedded in the image).

To **override defaults**, add environment variables in `docker-compose.yml`:

```yaml
environment:
  - APP_ENV=prod              # Required - loads .env.prod defaults
  - LOG_LEVEL=INFO            # Override: Change log verbosity
  - CACHE_TTL_SECONDS=3600    # Override: Cache duration (seconds)
  - ROOT_PATH=/kanso          # Override: Reverse proxy path prefix
```

To **change the port**, modify the port mapping (not environment variables):

```yaml
ports:
  - "8080:9525"  # Access on http://localhost:8080
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

The application will start on `http://localhost:9525`.

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

If port 9525 is already taken on your host machine, change the **host port** (left side) in `docker-compose.yml`:

```yaml
ports:
  - "8080:9525"  # Access on http://localhost:8080 instead
```

The container always uses port 9525 internally.

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

Clear browser storage and cookies for `localhost:9525` if you see authentication issues.

## Updating Kanso

### Docker (Pre-built Image)

```bash
# Pull latest image
docker compose pull

# Restart with new image
docker compose up -d
```

### Docker (Local Build)

If you're building locally from source:

```bash
# Pull latest code
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

# Remove downloaded image
docker rmi ghcr.io/dstmrk/kanso:latest
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
