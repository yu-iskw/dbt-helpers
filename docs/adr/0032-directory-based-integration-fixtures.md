# 32. Directory-Based Integration Fixtures for Warehouse Plugins

Date: 2026-02-17

## Status

Accepted

## Context

ADR 0031 introduced "Scenario-Driven Integration Testing" which allowed defining test states in code. However, defining complex dbt projects (with multiple models, seeds, and configurations) entirely in code via string dictionaries becomes unwieldy and hard to maintain for realistic end-to-end scenarios.

Specifically, we want to test how `dbt-helpers` handles:

1. Projects with nested directory structures.
2. Projects with complex `dbt_project.yml` settings.
3. Realistic projects like `jaffle_shop` to ensure compatibility with standard dbt patterns.

We need a way to support "Directory Scenarios" that load an existing dbt project from disk while still benefiting from the isolation and caching infrastructure provided by the Scenario framework.

## Decision

We will extend the Scenario framework to support directory-based fixtures.

1.  **DirectoryScenario Class**: Create a new `DirectoryScenario` class that inherits from `Scenario`.
    - It will take a `base_path` pointing to a directory containing a dbt project.
    - Instead of holding models/seeds in memory, it will reference them on disk.
2.  **Registration**: Directory scenarios will be registered in the `ScenarioRegistry` alongside code-based scenarios.
3.  **Fixture Integration**:
    - The `dbt_duckdb_container` fixture will detect if a scenario is a `DirectoryScenario`.
    - For `DirectoryScenario`, the workspace for the dbt build will be initialized by copying the fixture directory instead of writing strings to disk.
4.  **Hashing and Caching**:
    - The hash for a `DirectoryScenario` will be calculated based on the recursive hash of all files in the fixture directory (excluding temporary/build artifacts).
    - This ensures that any change in the fixture files triggers a cache miss and a rebuild of the integration test database.

## Consequences

### Positive

- **Realism**: Tests can run against actual dbt projects that look and feel like real-world setups.
- **Maintainability**: Complex projects can be maintained as standard dbt projects in a `fixtures` directory, allowing the use of IDE features and standard dbt commands during fixture development.
- **Consistency**: Reuses the existing caching and containerization logic from ADR 0031.

### Negative

- **Storage**: Fixture directories take up more space in the repository than string-based scenarios.
- **Complexity**: Hashing a directory recursively is slightly more complex than hashing a dictionary of strings.
