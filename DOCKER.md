# 🐳 Docker Deployment Guide

This guide explains how to deploy Kanso using Docker for **production use**.

> **For development**, use local mode with `uv run main.py` (faster, with hot-reload).
> **For deployment**, use Docker (optimized, production-ready).

## 📋 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Google Sheets credentials JSON (you'll configure this via the web UI)
- Your Google Sheets workbook URL

### Initial Setup

1. **Run the application**

   ```bash
   docker compose up -d
   ```

2. **Access the app**

   Open your browser at: http://localhost:6789

3. **Complete onboarding**

   On your first visit, Kanso will guide you through a 3-step setup:
   - **Welcome** - Introduction to the setup
   - **Credentials** - Paste your Google Service Account JSON credentials
   - **Configuration** - Enter your Google Sheet URL

   Your credentials are stored securely in encrypted user storage - **no files or environment variables needed**!

## 🔧 Configuration

### Auto-Loading Environment Files

The app automatically loads the correct configuration based on your environment:

```
APP_ENV=dev (default)  →  Loads .env.dev + .env.dev.local
APP_ENV=prod           →  Loads .env.prod + .env.prod.local
```

**Priority** (later overrides earlier):
1. `.env.{env}` - Template with defaults
2. `.env.{env}.local` - Your personal overrides
3. Explicitly set environment variables

This means you can simply run `uv run main.py` for development! 🎉

### Environment Files

The project uses a `.local` pattern for managing sensitive data:

| File | Purpose | Committed? |
|------|---------|------------|
| `.env.dev` | Dev template with defaults | ✅ Yes |
| `.env.dev.local` | Your dev overrides | ❌ No (gitignored) |
| `.env.prod` | Prod template with defaults | ✅ Yes |
| `.env.prod.local` | Your prod overrides | ❌ No (gitignored) |

### Key Differences: Local Dev vs Docker Prod

| Setting | Local Dev (`uv run main.py`) | Docker Prod |
|---------|-------------------------------|-------------|
| **Environment** | `.env.dev` + `.env.dev.local` | `.env.prod` + `.env.prod.local` |
| **Hot-reload** | ✅ Enabled | ❌ Disabled |
| **Logging** | DEBUG | WARNING |
| **Cache TTL** | 60s (1 min) | 86400s (24h) |
| **Deployment** | Native Python | Containerized |

## 🚀 Usage

### Development (Local)

For **active development** with hot-reload:

```bash
uv run main.py
```

> **Note**: Auto-loads `.env.dev` + `.env.dev.local`. Hot-reload enabled, debug mode on.

### Production (Docker)

For **deployment** with Docker:

```bash
# Start
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f kanso

# Rebuild after updates
docker compose build
docker compose up -d
```

> **Note**: Runs in production mode with optimized settings (no reload, minimal logging).

## 🔐 Security Notes

- Google Sheets credentials are stored in **encrypted user storage** (not in files)
- `.env.*.local` files are gitignored (safe for sensitive data)
- Non-root user (`kanso`) runs the app in Docker
- Storage secret is auto-generated and persisted for encryption
- No credential files needed in the container

## 📁 Volume Mounts

Docker mounts the following:
- `./.env.prod.local:/app/.env.prod.local:ro` - Local config overrides (read-only, optional)
- Storage secret and user data are persisted via Docker volumes

## 🩺 Health Check

The container includes a health check that runs every 30 seconds:
```bash
docker ps  # Check HEALTH status
```

## 🛠️ Troubleshooting

**Container won't start?**
- Check logs: `docker compose logs kanso`
- Verify port is not already in use
- Ensure Docker has enough resources allocated

**Port already in use?**
- Change `APP_PORT` in `.env.prod.local`
- Update port mapping in `docker-compose.yaml`

**Need to debug Docker build?**
- For development, use local mode: `uv run main.py` (faster iteration)
- To test Docker locally with dev settings: `docker run -e APP_ENV=dev ...`

## 📊 Environment Variables Reference

See `.env.dev` and `.env.prod` for full list of available options.

Key variables:
- `APP_ENV` - Environment (dev/prod)
- `DEBUG` - Debug mode (true/false)
- `LOG_LEVEL` - Logging level (DEBUG/INFO/WARNING/ERROR)
- `RELOAD` - Hot-reload (true/false)
- `APP_PORT` - Server port (default: 6789)
- `CACHE_TTL_SECONDS` - Cache time-to-live
- `ROOT_PATH` - Reverse proxy path prefix

> **Note**: Google Sheets credentials and workbook URL are configured through the web UI during onboarding, not via environment variables.

## 🔄 Updating

To update to a new version:
```bash
git pull
docker compose build
docker compose up -d
```
