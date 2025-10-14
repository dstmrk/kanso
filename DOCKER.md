# 🐳 Docker Setup Guide

This guide explains how to run Kanso using Docker for both development and production environments.

## 📋 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Google Sheets credentials JSON file
- Your Google Sheets workbook URL

### Initial Setup

1. **Configure environment**

   Edit `.env.dev.local` and/or `.env.prod.local` with your data:
   ```bash
   WORKBOOK_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/
   ROOT_PATH=/your/proxy/path  # Optional, leave empty if not using reverse proxy
   ```

2. **Add credentials**

   Copy your Google Sheets credentials JSON file to:
   ```
   config/credentials/gsheet_credentials.json
   ```

3. **Run the application**

   **Production mode** (default):
   ```bash
   docker-compose --profile prod up -d
   ```

   **Development mode** (with hot-reload):
   ```bash
   docker-compose --profile dev up
   ```

4. **Access the app**

   Open your browser at: http://localhost:6789

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

### Key Differences: Dev vs Prod

| Setting | Dev | Prod |
|---------|-----|------|
| **Hot-reload** | ✅ Enabled | ❌ Disabled |
| **Logging** | DEBUG | WARNING |
| **Cache TTL** | 60s | 24h |
| **Welcome message** | Shown | Hidden |

## 🚀 Usage

### Running Locally (without Docker)

**Development** (default):
```bash
uv run main.py
```

**Production**:
```bash
APP_ENV=prod uv run main.py
```

> **Note**: The app auto-loads `.env.{env}` and `.env.{env}.local` files based on the `APP_ENV` environment variable (defaults to `dev`)

### Docker Commands

**Start production** (detached):
```bash
docker-compose --profile prod up -d
```

**Start development** (with logs):
```bash
docker-compose --profile dev up
```

**Stop services**:
```bash
docker-compose down
```

**Rebuild after code changes**:
```bash
docker-compose --profile prod build
docker-compose --profile prod up -d
```

**View logs**:
```bash
docker-compose logs -f kanso       # Production
docker-compose logs -f kanso-dev   # Development
```

## 🔐 Security Notes

- Credentials folder is mounted **read-only** in Docker
- `.env.*.local` files are gitignored (safe for sensitive data)
- Non-root user (`kanso`) runs the app in Docker
- Storage secret is auto-generated and persisted

## 📁 Volume Mounts

### Production
- `./config/credentials:/app/config/credentials:ro` - Credentials (read-only)
- `./.env.prod.local:/app/.env.prod.local:ro` - Local overrides (read-only)

### Development (additional)
- `./app:/app/app` - Source code (hot-reload)
- `./main.py:/app/main.py` - Main file (hot-reload)
- `./static:/app/static` - Static files

## 🩺 Health Check

The container includes a health check that runs every 30 seconds:
```bash
docker ps  # Check HEALTH status
```

## 🛠️ Troubleshooting

**Container won't start?**
- Check credentials file exists: `ls config/credentials/`
- Verify `.env.*.local` files have correct values
- Check logs: `docker-compose logs kanso`

**Port already in use?**
- Change `APP_PORT` in `.env.*.local`
- Update port mapping in `docker-compose.yaml`

**Hot-reload not working in dev?**
- Ensure you're using the `dev` profile
- Check volumes are mounted correctly
- Verify `RELOAD=true` in `.env.dev`

## 📊 Environment Variables Reference

See `.env.dev` and `.env.prod` for full list of available options.

Key variables:
- `APP_ENV` - Environment (dev/prod)
- `DEBUG` - Debug mode (true/false)
- `LOG_LEVEL` - Logging level (DEBUG/INFO/WARNING/ERROR)
- `RELOAD` - Hot-reload (true/false)
- `APP_PORT` - Server port (default: 6789)
- `CACHE_TTL_SECONDS` - Cache time-to-live
- `WORKBOOK_URL` - Google Sheets URL
- `ROOT_PATH` - Reverse proxy path prefix

## 🔄 Updating

To update to a new version:
```bash
git pull
docker-compose --profile prod build
docker-compose --profile prod up -d
```
