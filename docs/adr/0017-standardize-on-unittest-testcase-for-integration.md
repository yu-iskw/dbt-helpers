# 17. Standardize on unittest.TestCase for Integration Tests

Date: 2026-02-16

## Status

Accepted

## Context

Following ADR-0015, we standardized unit tests to use `unittest.TestCase`. However, integration tests were still using `pytest` functional style with fixture injection (e.g., `tmp_path`, `dbt_duckdb_container`).

To achieve complete consistency across the test suite and ensure that all tests benefit from:

1. Structural rigidity (classes).
2. Explicit lifecycle management (`setUp`, `tearDown`, `setUpClass`).
3. Portability (executable via `python -m unittest`).
4. Reduced reliance on `pytest`-specific magic in test definitions.

We need to extend the standardization to integration tests.

## Decision

We will standardize all integration tests to use `unittest.TestCase`.

1. **Base Class**: We will introduce an `IntegrationTestCase` base class in `dbt_helpers_core.testing` to provide common integration utilities (like temporary directory management) without relying on `pytest` fixtures.
2. **Setup/Teardown**:
   - Use `setUpClass` and `tearDownClass` for resource-heavy setup (like database container initialization or `dbt build` runs).
   - Use `setUp` and `tearDown` for per-test isolation (like temporary project directories).
3. **Assertions**: Use `self.assert*` methods instead of bare `assert`.
4. **Fixture Migration**: Replace `pytest` fixtures (e.g., `tmp_path`) with standard library equivalents (e.g., `tempfile.TemporaryDirectory`) managed within the `TestCase` lifecycle.

## Consequences

- **Consistency**: The entire test suite (unit and integration) now follows the same pattern.
- **Improved Portability**: Integration tests can be run independently of the `pytest` runner if needed.
- **Explicit Lifecycle**: Database setup and cleanup are explicitly managed in `setUpClass`, making the test flow easier to trace.
- **Refactoring Effort**: Existing integration tests in warehouse plugins (e.g., DuckDB) must be refactored.
- **Library Dependency**: Warehouse plugins will depend on `dbt_helpers_core.testing` for the base class.
