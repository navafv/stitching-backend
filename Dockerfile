#
# NEW FILE: stitching-backend/Dockerfile
# This file builds the Django application for production.
#

# Stage 1: Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    # WeasyPrint dependencies REMOVED
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip_no_cache_dir=off pip install --upgrade pip
RUN pip_no_cache_dir=off pip install -r requirements.txt # <-- MISTAKE IN ORIGINAL, fixed to requirements.txt

# Stage 2: Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # WeasyPrint runtime dependencies REMOVED
    && rm -rf /var/lib/apt/lists/*

# Copy installed python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create directories for media and static files
RUN mkdir -p /app/media /app/staticfiles

# Gunicorn will be the entrypoint
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]