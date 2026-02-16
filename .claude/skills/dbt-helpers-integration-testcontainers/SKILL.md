---
name: dbt-helpers-integration-testcontainers
description: Set up and run integration tests using Testcontainers. Use when testing warehouse adapters against real database engines or verifying filesystem-dependent operations.
---

# dbt-helpers-integration-testcontainers

## Purpose

To verify that our adapters work correctly against real infrastructure, ensuring that SQL dialect nuances, connection edge cases, and filesystem behaviors are correctly handled.

## Core Principles

1. **Isolation**: Each test session should have its own clean container instance.
2. **Reproducibility**: Use specific image tags (e.g., `duckdb:latest`, `postgres:15`) to ensure consistent results.
3. **Efficiency**: Use pytest fixtures with `session` or `module` scope where appropriate to minimize container startup overhead.

## Patterns

### 1. Database Fixture

```python
@pytest.fixture(scope="session")
def duckdb_container():
    with DuckDBContainer("duckdb/duckdb:latest") as duckdb:
        yield duckdb

@pytest.fixture
def catalog_client(duckdb_container):
    return DuckDBCatalogClient(connection_url=duckdb_container.get_connection_url())
```

### 2. Cleanup

Always ensure containers are stopped and resources are cleaned up using context managers or `yield` fixtures.

## Instructions

### When writing integration tests

1. Locate tests in `src/<package>/tests/integration/`.
2. Use `testcontainers-python` for managing Docker instances.
3. Verify the adapter's behavior against the real engine (e.g., check that BQ partition info is correctly extracted).

### When implementing a new warehouse adapter

1. Create a corresponding integration test in the plugin package.
2. Test both "happy path" and common failure modes (e.g., table not found, permission denied).

## References

- [ADR 0006: Nullable Infrastructure Testing Strategy](../../../docs/adr/0006-nullable-infrastructure-testing-strategy.md)
- [Testcontainers for Python Documentation](https://testcontainers-python.readthedocs.io/)
