FROM python:3.12-slim

# Install dbt-duckdb and dependencies
RUN pip install --no-cache-dir dbt-duckdb ruamel.yaml

# Set working directory
WORKDIR /workspace

# Copy the sample project fixture into the image
# This allows the container to run independently if needed
# When running via testcontainers, volumes can override this
COPY fixtures/sample_project /workspace

# Non-root user for security scanners (Trivy DS002)
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /workspace
USER appuser

# Trivy DS026: test fixture image, not a long-running service
HEALTHCHECK NONE

# Default command: build the dbt project
# This will generate the .duckdb file
# The output path can be overridden via DBT_PROFILES_DIR environment variable
ENTRYPOINT ["dbt", "build", "--project-dir", "/workspace"]
