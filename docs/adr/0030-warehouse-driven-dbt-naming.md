# 30. Warehouse-Driven dbt Resource Naming

Date: 2026-02-16

## Status

Proposed

## Context

Different data warehouses have different naming conventions and hierarchies (e.g., BigQuery's 3-tier `project.dataset.table` vs. DuckDB's 2-tier `schema.table`). Previously, the logic for generating dbt resource names (for models and sources) was embedded within Jinja2 templates. This made templates warehouse-specific and difficult to maintain as more warehouses were added.

Specifically, dbt models and sources need unique identifiers within the dbt project. When importing multiple sources from different databases or projects, name collisions are likely if only the raw table name is used.

## Decision

We will move the responsibility for defining dbt-compatible resource names from the schema templates to the warehouse plugins.

1. **SDK Update**: Add a `dbt_name` field to the `CatalogRelation` model in the SDK. This allows warehouse plugins to provide an "opinionated" name for dbt.
2. **Core Update**: The `resource_mapper` will prioritize `rel.dbt_name` when creating the version-agnostic `DbtResourceIR`.
3. **Plugin Implementation**: Warehouse plugins (like DuckDB) will implement their specific naming logic (e.g., `schema__table`) during the `read_catalog` phase.
4. **Template Simplification**: Schema templates (like `source.yml.j2`) will use `resource.name` directly for the dbt resource name, remaining warehouse-agnostic. The raw warehouse identifier will be stored in `_extraction_metadata.identifier`.

## Consequences

### Positive

- **Warehouse Agnostic Templates**: Templates no longer need to know how to construct names for different warehouses.
- **Collision Avoidance**: Warehouse plugins can ensure names are unique and follow dbt's valid identifier rules.
- **Flexibility**: Custom naming rules can be implemented per warehouse without affecting other parts of the system.

### Negative

- **Plugin Responsibility**: Warehouse plugin authors must now consider how names should appear in dbt.
- **IR Dependency**: The IR `name` field now represents the _dbt_ name, while the raw identifier is tucked away in metadata.
