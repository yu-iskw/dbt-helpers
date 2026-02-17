FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Use DBT_FLAVOR (core, fusion) and DBT_VERSION build args
ARG DBT_FLAVOR=core
ARG DBT_VERSION=1.11

# Set up environment for dbt Fusion if needed
ENV PATH="/root/.local/bin:${PATH}"

# Conditional installation logic
RUN if [ "$DBT_FLAVOR" = "core" ]; then \
        pip install --no-cache-dir "dbt-duckdb~=${DBT_VERSION}.0" ruamel.yaml; \
    elif [ "$DBT_FLAVOR" = "fusion" ]; then \
        curl -fsSL https://public.cdn.getdbt.com/fs/install/install.sh | sh && \
        pip install --no-cache-dir ruamel.yaml && \
        cp /root/.local/bin/dbt /usr/local/bin/dbt 2>/dev/null || true; \
    else \
        echo "Unknown DBT_FLAVOR: $DBT_FLAVOR" && exit 1; \
    fi

# Set working directory
WORKDIR /workspace

# Project files will be mounted via volume mapping in conftest.py

# Non-root user for security scanners (Trivy DS002)
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /workspace
USER appuser

# Trivy DS026: test fixture image, not a long-running service
HEALTHCHECK NONE

# Default command: build the dbt project
# This will generate the .duckdb file
ENTRYPOINT ["dbt", "build", "--project-dir", "/workspace"]
