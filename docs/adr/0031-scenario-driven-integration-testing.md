# 31. Scenario-Driven Integration Testing for Warehouse Plugins

Date: 2026-02-17

## Status

Proposed

## Context

Integration tests for warehouse plugins (like DuckDB) currently rely on a fixed `sample_project` fixture. This approach has several limitations:

1. **Brittle Fixtures**: Adding a test case that requires a new table or specific data requires modifying the global `sample_project`, which can break other tests.
2. **Performance**: Every test execution that requires a database must either recreate it from scratch or share a dirty state.
3. **Limited Coverage**: It's difficult to test edge cases (e.g., empty schemas, specific data types, name collisions) without cluttering the sample project.
4. **Slow Feedback**: Running dbt build in a container for every test run is slow.

We need a way to define localized "Scenarios" for integration tests that are independent, easy to maintain, and performant.

## Decision

We will implement a scenario-driven integration testing framework.

1. **Scenario Definition**: Introduce a `Scenario` dataclass that encapsulates:
   - `name`: Unique identifier for the scenario.
   - `models`: Dictionary of model names to their SQL content.
   - `seeds`: Dictionary of seed names to their CSV content.
   - `project_vars`: Key-value pairs for `dbt_project.yml`.
2. **Registry**: Scenarios will be defined in a dedicated directory (e.g., `tests/integration/scenarios/`) and registered in a central registry.
3. **Parameterized Fixtures**: Update the `dbt_duckdb_container` fixture in `conftest.py` to accept a `scenario` parameter.
4. **Caching Strategy**:
   - The fixture will calculate a hash of the scenario content.
   - It will check a local cache (e.g., `.tests/cache/duckdb/`) for an existing `.duckdb` file matching the hash.
   - If a cache hit occurs, it uses the existing file, saving the dbt build time.
   - If a cache miss occurs, it runs dbt build, saves the resulting file to the cache, and provides it to the test.

## Consequences

### Positive

- **Independence**: Tests can define their own state without side effects on other tests.
- **Speed**: Caching eliminates redundant dbt builds, significantly speeding up the test suite.
- **Maintainability**: Scenarios are defined in code (or small fixtures), making them easier to read and modify.
- **Thoroughness**: Easily test many permutations of database state.

### Negative

- **Complexity**: Adds a new layer of abstraction for test setup.
- **Disk Usage**: The cache directory will grow over time (requires a cleanup strategy).
- **Inconsistency Risk**: If the hash function doesn't capture all relevant changes (e.g., dbt version changes), tests might use stale databases.
