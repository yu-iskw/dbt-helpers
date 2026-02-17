# 20. Sync and Scaffold Strategy

Date: 2026-02-16

## Status

Accepted

## Context

The `dbt-helpers` tool currently supports initial source import and model scaffolding. However, dbt projects evolve: columns are added to warehouse tables, and types change. We need a way to synchronize existing dbt YAML properties with the warehouse state without overwriting manual documentation or custom configurations. Additionally, we want to expand scaffolding to include dbt snapshots.

## Decision

We will implement a synchronization and scaffolding engine that follows the established Hexagonal pattern:

1.  **Sync-via-Patch Strategy**:

    - Instead of full YAML regeneration, we will use a "diff-and-patch" approach.
    - **Core Flow**:
      1. Read Warehouse Catalog (`CatalogRelation`).
      2. Read existing dbt YAML and parse into internal IR (`DbtResourceIR`).
      3. Diff the Warehouse Catalog against the dbt IR.
      4. Generate a set of `PlannedOp` (specifically `UpdateYamlFile`) containing fine-grained patches.
    - **Safety**: Preservation of YAML comments and manually added metadata (like custom tests or tags) is paramount. We will use `ruamel.yaml` via the `YamlStore` to apply these patches safely.

2.  **Snapshot Scaffolding**:

    - We will implement `dbth snapshot scaffold` to generate dbt snapshot SQL files.
    - The scaffold will include a default snapshot configuration (e.g., `check_cols` or `updated_at` strategy).

3.  **SDK Extensions**:
    - `SchemaAdapter` will be extended to support `parse_source_yaml` and `parse_model_yaml` to enable the "Sync" flow.
    - `SchemaAdapter` will also support `render_snapshot_sql`.

## Consequences

- **Reduced Maintenance Overhead**: `source sync` and `model sync` automate the tedious task of keeping YAML files up to date with warehouse changes.
- **Improved Metadata Integrity**: By using patches instead of full renders, we ensure that manual documentation and custom YAML configurations are preserved.
- **Consistency**: Centralized scaffolding logic ensures that all dbt resources (sources, models, snapshots) follow the same patterns and naming conventions defined in `dbt_helpers.yml`.
- **Complexity**: Implementing a robust diffing and patching engine is more complex than simple code generation but provides significantly higher value for long-lived projects.
