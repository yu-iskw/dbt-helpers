---
name: dbt-helpers-plugin-scaffold
description: Scaffold and standardize new dbt-helpers plugins (Warehouse, Tool, or Schema). Use when starting a new plugin implementation or updating plugin discovery configuration.
---

# dbt-helpers-plugin-scaffold

## Purpose

To maintain a consistent structure across all `dbt-helpers` plugins and ensure they are correctly registered via Python entry points.

## Plugin Types

1. **Warehouse Plugins**: Implement `CatalogClient` to read metadata.
2. **Tool Plugins**: Implement `Emitter` to generate `PlannedOp` objects.
3. **Schema Plugins**: Implement `SchemaAdapter` for dbt YAML mapping.

## Standard Directory Structure

```text
src/plugins/<category>/dbt_helpers_<type>_<name>/
├── pyproject.toml
├── src/
│   └── dbt_helpers_<type>_<name>/
│       ├── __init__.py
│       └── plugin.py
└── tests/
    ├── unit/
    └── integration/
        ├── conftest.py
        └── Dockerfile
```

## Implementation Knowledge (Warehouse Plugins)

### 1. `pyproject.toml` Specification

- **Name**: `dbt-helpers-<type>-<name>` (e.g., `dbt-helpers-wh-bigquery`).
- **Dependencies**: Must include `dbt-helpers-sdk`.
- **Entry Points**: Register under `[project.entry-points."dbt_helpers.warehouse_plugins"]`.
- **Workspace Sources**: Use `{ workspace = true }` for local `dbt-helpers-sdk` during development.

### 2. `plugin.py` Specification

- Inherit from `dbt_helpers_sdk.CatalogClient`.
- Implement `read_catalog(self, scope: list[str], connection_config: dict[str, Any]) -> list[CatalogRelation]`.
- Use `CatalogRelation`, `CatalogNamespace`, and `CatalogColumn` models from SDK.

### 3. Integration Testing (`tests/integration/`)

- **`Dockerfile`**: Should set up a dbt environment with the relevant adapter (e.g., `dbt-postgres`).
- **`conftest.py`**:
  - Use `dbt_helpers_sdk.testing.DbtRunner` for executing dbt.
  - Use `dbt_helpers_sdk.testing.ScenarioRegistry` to define test dbt projects.
  - Implement a `dbt_container` fixture that yields a configured database instance.

## Instructions

### When creating a new plugin

1. **Initialize Directory**: Create the package directory under `src/plugins/<category>/` using the naming convention `dbt_helpers_<type>_<name>`.
2. **Implement SDK Interface**: Create `src/dbt_helpers_<type>_<name>/plugin.py` and implement the required methods.
3. **Configure Package**: Create `pyproject.toml` with the standard metadata and entry point registration.
4. **Set Up Tests**:
   - Create `tests/unit/` for mocking logic.
   - Create `tests/integration/` with a `Dockerfile` and `conftest.py` leveraging the `dbt-helpers-sdk.testing` module.
5. **Reference Gold Standard**: Always refer to `src/plugins/warehouses/dbt_helpers_wh_duckdb` for the most up-to-date implementation patterns.

### Validation Checklist

- Does it depend only on `dbt-helpers-sdk` (and external libs)?
- Are tests co-located in the package?
- Is the naming convention followed (`dbt_helpers_<type>_<name>`)?
- Are `dbt_helpers_sdk.testing` utilities used in integration tests?

## References

- [ADR 0007: Categorized Plugin Directory Structure](../../../docs/adr/0007-categorized-plugin-directory-structure.md)
- [System Design: Plugin-First](../../../docs/core/system_design.md#plugin-first)
- [SDK Testing Utilities](../../../src/dbt_helpers_sdk/src/dbt_helpers_sdk/testing/)
