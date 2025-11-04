# Configuration Guide

Customize Kanso's behavior, appearance, and data sources through environment variables and application settings.

## Environment Variables

Kanso works out-of-the-box with sensible defaults. All configuration is **optional**.

To customize settings, create a `.env` file in the project root:

```bash
# Environment (dev/prod)
APP_ENV=prod

# Debug mode
DEBUG=false

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=WARNING

# Hot-reload on code changes (development only)
RELOAD=false

# Application port
APP_PORT=9525

# Application title
APP_TITLE="kanso - your minimal money tracker"

# Default theme (light/dark)
DEFAULT_THEME=light

# Cache duration in seconds (24 hours = 86400)
CACHE_TTL_SECONDS=86400

# Reverse proxy path (leave empty if not using proxy)
ROOT_PATH=
```

### Common Settings

#### `APP_ENV`

**Purpose:** Application environment

**Options:** `dev`, `prod`

**Default:** `prod`

**Effect:** Changes logging behavior and cache duration

#### `LOG_LEVEL`

**Purpose:** Controls application logging verbosity

**Options:** `DEBUG`, `INFO`, `WARNING`, `ERROR`

**Default:** `WARNING` (prod), `DEBUG` (dev)

**Log Levels:**

| Level    | When to Use                              |
|----------|------------------------------------------|
| DEBUG    | Development - see all operations         |
| INFO     | Production - normal operational messages |
| WARNING  | Production - potential issues only       |
| ERROR    | Production - errors only                 |

#### `APP_PORT`

**Purpose:** HTTP port for the web server

**Default:** `9525`

**Example:**
```bash
APP_PORT=8080
```

Update `docker-compose.yml` if you change this:
```yaml
ports:
  - "8080:8080"  # Match the APP_PORT value
```

#### `CACHE_TTL_SECONDS`

**Purpose:** How long to cache processed financial data

**Default:** `86400` (24 hours in prod), `60` (1 minute in dev)

**Example:**
```bash
CACHE_TTL_SECONDS=3600  # 1 hour
```

## Application Settings

Settings configured via the web UI are stored in **browser local storage** and are user-specific.

### Currency

**Location:** Settings page

**Supported Currencies:**

| Code | Currency          | Symbol | Decimal |
|------|-------------------|--------|---------|
| EUR  | Euro              | €      | Comma   |
| USD  | US Dollar         | $      | Dot     |
| GBP  | British Pound     | £      | Dot     |
| CHF  | Swiss Franc       | Fr     | Comma   |
| JPY  | Japanese Yen      | ¥      | None    |

**Effects:**
- Chart axis labels and tooltips
- Number formatting (1.234,56 vs 1,234.56)
- Currency symbols in UI

**Change currency:**
1. Open Settings (gear icon in sidebar)
2. Select new currency from dropdown
3. Click **Save**
4. Dashboard will update automatically

### Google Sheets Credentials

**Location:** Onboarding wizard or Settings → Data

**Required Information:**
- Service Account JSON (entire file content)
- Google Sheet URL

**To update:**
1. Go to Settings → Data
2. Click **Update Credentials**
3. Paste new JSON and/or Sheet URL
4. Click **Save**

**Security Notes:**
- Credentials are stored in browser local storage only
- Persist across sessions (you don't need to re-enter credentials on each visit)
- Never sent to external servers (only to Google Sheets API)
- Only cleared when you explicitly clear browser data or use a different browser/device

## Data Management

### Refresh Data

Kanso loads data from **browser storage** for fast page loads. Data is fetched from Google Sheets only when:

- First-time onboarding setup
- Manual refresh (Settings → Data → Refresh Data button)

**Manual refresh:**
1. Go to Settings → Data
2. Click **Refresh Data**
3. Kanso checks for changes and updates only modified sheets
4. View which sheets were updated in the result dialog

**Smart refresh:** Only sheets with changes are reloaded (hash-based detection)

### Cache Settings

Kanso caches **processed financial data** in memory for **24 hours**.

**What's cached:**
- Preprocessed DataFrames (dates parsed, amounts converted)
- Calculated metrics (net worth, savings ratio, etc.)

**Clear cache:**
1. Go to Settings → Data
2. Click **Clear Cache**
3. Financial calculations will be recomputed on next page load

!!! note "Data vs Cache"
    - **Data** (in browser storage): Raw Google Sheets data persists across sessions
    - **Cache** (in memory): Processed calculations, cleared on browser close or TTL expiry

### Data Quality Checks

Kanso validates your sheet structure on every data load:

- Missing required sheets (Assets, Liabilities, Incomes, Expenses)
- Empty sheets
- Missing required columns

**View warnings:**
- Dashboard shows warning banner if data quality issues detected
- Click warning for details

## Docker Configuration

### Docker Compose

Edit `docker-compose.yml` to customize deployment:

```yaml
services:
  kanso:
    build: .
    ports:
      - "${APP_PORT:-9525}:9525"
    environment:
      - APP_ENV=${APP_ENV:-prod}
      - LOG_LEVEL=${LOG_LEVEL:-WARNING}
    volumes:
      - ./kanso-data:/app/data  # Persistent storage
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9525/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Volume Mounts

**Data directory:**
```yaml
volumes:
  - ./kanso-data:/app/data
```

- Stores cache and temporary files
- Survives container restarts
- Backup this directory for disaster recovery

**Custom location:**
```yaml
volumes:
  - /path/to/your/data:/app/data
```

## Advanced Configuration

### Custom Port Binding

Bind to specific network interface:

```yaml
ports:
  - "127.0.0.1:9525:9525"  # Localhost only
```

Use with reverse proxy (nginx, Caddy) for HTTPS.

### Behind a Reverse Proxy

Example nginx configuration:

```nginx
server {
    listen 80;
    server_name kanso.yourdomain.com;

    location / {
        proxy_pass http://localhost:9525;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Add SSL with Let's Encrypt:

```bash
certbot --nginx -d kanso.yourdomain.com
```

### Environment from File

Load environment from external file:

```yaml
services:
  kanso:
    env_file:
      - .env
      - .env.local  # Overrides
```

## Troubleshooting

### Settings Not Persisting

**Cause:** Browser storage cleared or disabled

**Fix:**
1. Check browser privacy settings
2. Allow local storage for `localhost:9525`
3. Try incognito/private mode to test

### Port Already in Use

**Cause:** Another service using port 9525

**Fix:**
```bash
# Check what's using the port
lsof -i :9525

# Change port in .env
APP_PORT=8080

# Restart Kanso
docker compose down && docker compose up -d
```

### Credentials Lost After Update

**Cause:** Browser storage cleared during update

**Fix:**
- Re-enter credentials via Settings → Data
- Credentials are stored only in browser for security (not on server)

## Next Steps

- **[Google Sheets Setup](google-sheets-setup.md)** - Configure your data source
- **[Architecture](architecture.md)** - Understand how Kanso processes data
- **[API Reference](api-reference.md)** - Deep dive into data models
