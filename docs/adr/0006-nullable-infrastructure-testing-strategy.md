# 6. Nullable Infrastructure Testing Strategy

Date: 2026-02-16

## Status

Accepted

## Context

The `dbt-helpers` project requires a testing strategy that ensures high confidence, speed, and reproducibility. Traditional testing approaches often rely heavily on mocks (which can be brittle and hide bugs) or slow integration tests against real cloud warehouses (which require network access and credentials).

We need a strategy that:

1. **Ensures Idempotency**: Testing environments should be clean and predictable.
2. **Minimizes Mocks**: Prefer real implementations or verified fakes over standard mocking libraries.
3. **Supports Local & CI/CD**: Tests must run without external warehouse access.
4. **Is Modular**: Tests should be co-located with their respective packages.
5. **Is Extensible**: Easy to add support for remote warehouses (Snowflake, BigQuery) later.

## Decision

We will adopt the **Nullable Infrastructure** pattern (as described by James Shore) combined with **Testcontainers** for integration testing.

### Key Components

1. **Functional Core, Imperative Shell**:

   - **Core Logic**: Pure domain logic, orchestrators, and plan engines will be "pure" (no I/O). They will be tested with standard unit tests.
   - **Infrastructure Adapters**: All external side effects (Filesystem, Warehouse Catalog, CLI output) will be hidden behind stable interfaces (Protocols/ABCs).

2. **Nullable Adapters (Unit Testing)**:

   - Instead of using `unittest.mock.patch`, we will implement "Nullable" versions of our infrastructure adapters.
   - A Nullable adapter is a real, production-ready implementation that has an internal "off switch" or use an in-memory substitute (like DuckDB in-memory or a dictionary-based store).
   - These will be used in unit tests to provide fast, deterministic, and mock-free testing of business logic.

3. **Integration Tests with Testcontainers**:

   - Real implementations of adapters (e.g., `PostgresCatalogClient`, `DuckDBFileSystemAdapter`) will be tested against actual instances using Docker containers.
   - `testcontainers-python` will be used to manage the lifecycle of these containers programmatically within `pytest` fixtures.

4. **Package-Colocated Tests**:
   - Tests will move from the root `./tests` directory into their respective packages: `src/<package>/tests/`.
   - `unit/` subdirectories will contain mock-free logic tests.
   - `integration/` subdirectories will contain container-based adapter tests.

## Consequences

- **High Confidence**: Tests run against real database engines (DuckDB/Postgres) or verified fakes.
- **Speed**: Logic tests are extremely fast as they avoid container startup and network I/O.
- **Maintainability**: No brittle mocks to update when internal implementation details change.
- **Scalability**: Adding a new warehouse like BigQuery only requires implementing a new adapter and its corresponding integration tests; the core logic remains tested via the existing Nullable patterns.
- **Infrastructure Overhead**: Requires initial effort to build stable interfaces and Nullable implementations.
