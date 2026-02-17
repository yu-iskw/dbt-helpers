---
name: dbt-helpers-path-policy
description: Manage and enforce path templating and naming conventions in dbt-helpers. Use when implementing PathPolicy, defining template variables, or configuring warehouse-specific defaults.
---

# dbt-helpers-path-policy

## Purpose

To ensure consistent and predictable file locations and resource names across different dbt projects and warehouses.

## Templating System

- **Syntax**: `{{ variable }}` (e.g., `models/{{ dataset }}/{{ table }}.sql`).
- **Logic**: Simple regex-based substitution (no Jinja2 dependencies).

## Available Variables

Derived from `CatalogRelation` and `CatalogNamespace`:

- `project` / `database`
- `dataset` / `schema`
- `table` / `identifier`
- `kind` (table, view, etc.)
- `namespace_0`, `namespace_1`, ... (positional parts)

## Instructions

### When implementing PathPolicy

1. Ensure that variables are correctly extracted from IR types.
2. Support overrides from `dbt_helpers.yml`.
3. Enforce that all resolved paths are within the project root.

### When defining warehouse defaults

1. BigQuery: `models/{{ project }}/{{ dataset }}/{{ kind }}/{{ table }}.sql`
2. DuckDB/Postgres: `models/{{ schema }}/{{ table }}.sql`

## References

- [System Design: Path and Naming Policy](../../../docs/core/system_design.md#path-and-naming-policy)
