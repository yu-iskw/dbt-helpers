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
```

## Instructions

### When creating a new plugin

1. Determine the correct category: `warehouses`, `tools`, or `schemas`.
2. Create the package directory under `src/plugins/<category>/`.
3. Define the plugin class inheriting from the appropriate SDK interface.
4. Register the plugin in `pyproject.toml` under the correct entry point:
   - `dbt_helpers.warehouse_plugins`
   - `dbt_helpers.tool_plugins`
   - `dbt_helpers.schema_plugins`

### Validation Checklist

- Does it depend only on `dbt-helpers-sdk` (and external libs)?
- Are tests co-located in the package?
- Is the naming convention followed (`dbt_helpers_<type>_<name>`)?

## References

- [ADR 0007: Categorized Plugin Directory Structure](../../../docs/adr/0007-categorized-plugin-directory-structure.md)
- [System Design: Plugin-First](../../../docs/core/system_design.md#plugin-first)
