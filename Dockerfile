# syntax=docker/dockerfile:1

# Build stage: Install dependencies
FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev dependencies for production)
RUN uv sync --frozen --no-dev --no-install-project

# Production stage: Minimal runtime image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 kanso && \
    chown -R kanso:kanso /app
USER kanso

# Expose default port
EXPOSE 6789

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD /app/.venv/bin/python -c "import urllib.request; urllib.request.urlopen('http://localhost:6789')"

# Default command
# Note: main.py automatically loads .env.{APP_ENV} based on APP_ENV environment variable
# Use venv python directly to avoid uv sync at runtime
CMD ["/app/.venv/bin/python", "main.py"]
