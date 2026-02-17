# 10. Plugin-level Docker Integration Testing

Date: 2026-02-16

## Status

Accepted

## Context

To ensure that warehouse adapters correctly interpret dbt-generated metadata, we need to test them against real database artifacts. Unit tests with in-memory DuckDB are insufficient for verifying complex behaviors that emerge from `dbt build` processes.

## Decision

We will implement plugin-level integration tests using a combination of sample dbt projects and real database engines.

1.  **Package-Colocated Integration Tests**: Integration tests reside in `src/plugins/warehouses/<plugin>/tests/integration/`.
2.  **dbt Project Fixtures**: Each integration test suite includes a minimal `sample_project` to generate the necessary database state.
3.  **Engine Orchestration**:
    - For local-file warehouses (like DuckDB), tests support both local execution and Docker-based execution:
      - **Local execution** (default): Runs `dbt build` locally for faster iteration during development.
      - **Docker execution**: Uses a Dockerfile and `testcontainers-python` to run `dbt build` in an isolated container, providing better reproducibility and CI/CD alignment. Controlled via `USE_DOCKER=true` environment variable.
    - For server-based warehouses (like Postgres), `testcontainers-python` is used to manage the lifecycle of the database engine within the test suite.
4.  **Verification**: The plugin's `read_catalog` method is executed against the real database, and the results are asserted against the expected dbt-defined schema.
5.  **Idempotency**: Integration tests verify that repeated executions produce identical results, ensuring deterministic behavior.

## Docker-based DuckDB Testing

For DuckDB integration tests, we provide a Dockerfile (`tests/integration/Dockerfile`) that:

- Uses `python:3.12-slim` as the base image
- Installs `dbt-duckdb` and dependencies
- Includes the sample dbt project fixture
- Runs `dbt build` to generate the database file

The Docker-based fixture (`dbt_duckdb_container_docker`) uses `testcontainers-python` to:

- Build the Docker image from the Dockerfile
- Mount volumes for the dbt project and output database
- Execute `dbt build` in the container
- Extract the generated `.duckdb` file to the host filesystem
- Ensure cleanup of containers and volumes

This approach provides:

- **Isolation**: Each test run uses a fresh container environment
- **Reproducibility**: Consistent dbt and Python versions across environments
- **CI/CD Alignment**: Tests run the same way in CI as locally
- **Idempotency**: Repeated runs produce identical database files

## Consequences

- **High Confidence**: Adapters are verified against the exact metadata format produced by dbt.
- **E2E Validation**: Provides a vertical slice of verification from dbt project build to dbt-helpers catalog extraction.
- **Complexity**: Requires a local installation of `dbt` and/or Docker for integration tests.
- **Isolation**: Each plugin maintains its own integration suite, preventing monolithic test failures.
- **Flexibility**: DuckDB tests can run locally for speed or in Docker for reproducibility, controlled via environment variable.
