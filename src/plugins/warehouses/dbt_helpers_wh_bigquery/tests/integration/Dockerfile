FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install dbt-bigquery
RUN pip install --no-cache-dir "dbt-bigquery"

# Create a fake keyfile for the emulator
RUN echo '{"type": "service_account", "project_id": "test"}' > /tmp/fake-key.json

# Set working directory
WORKDIR /workspace

# Project files will be copied into the image
COPY dbt_project/ /workspace/

# Set the profiles directory to current workspace
ENV DBT_PROFILES_DIR=/workspace

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /workspace
USER appuser

# Healthcheck not needed for transient runner
HEALTHCHECK NONE

# Default command: build the dbt project
CMD ["dbt", "build"]
