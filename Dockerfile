#
# Dockerfile for the Django application (Production)
# This uses a multi-stage build to keep the final image slim.
#

# --- Stage 1: Builder ---
# This stage installs build-time dependencies and Python packages
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies required for building Python packages
# (e.g., libpq-dev for psycopg2)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip_no_cache_dir=off pip install --upgrade pip
RUN pip_no_cache_dir=off pip install -r requirements.txt


# --- Stage 2: Final Image ---
# This stage builds the final, lightweight runtime image
FROM python:3.11-slim

WORKDIR /app

# Install only runtime system dependencies (if any)
# We remove WeasyPrint dependencies as it's replaced by xhtml2pdf
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code into the final image
COPY . .

# Create directories for media and static files (if they don't exist)
# These will typically be mounted as volumes in production.
RUN mkdir -p /app/media /app/staticfiles

# Expose the port Gunicorn will run on
EXPOSE 8000

# Run the application using Gunicorn
# Binds to all interfaces on port 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]