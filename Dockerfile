# Stage 1: Build the environment
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN pip install --upgrade pip

# Copy requirements and install packages
# This layer is cached as long as requirements.txt doesn't change
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Stage 2: Create the final, smaller image
FROM python:3.11-slim

WORKDIR /app

# Create a non-root user for security
RUN useradd --create-home appuser
USER appuser

# Copy installed packages from the builder stage
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy the application code
COPY --chown=appuser:appuser . .

# Expose the port NiceGUI runs on
EXPOSE 6789

# The command to run the application
# We use the host "0.0.0.0" to make it accessible outside the container
CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "6789"]