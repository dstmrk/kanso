# syntax=docker/dockerfile:1

# Build stage: Install dependencies
FROM python:3.13-slim AS builder

# Install uv (uvx not needed for dependency installation)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation for production performance
ENV UV_COMPILE_BYTECODE=1

# Use copy mode for reliable container behavior
ENV UV_LINK_MODE=copy

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies with cache mount for faster builds
# --frozen: Use exact versions from lock file
# --no-dev: Skip dev dependencies
# --no-install-project: Only install dependencies, not the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

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
EXPOSE 9525

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD /app/.venv/bin/python -c "import urllib.request; urllib.request.urlopen('http://localhost:9525')"

# Default command
# Note: main.py automatically loads .env.{APP_ENV} based on APP_ENV environment variable
# Use venv python directly to avoid uv sync at runtime
CMD ["/app/.venv/bin/python", "main.py"]
