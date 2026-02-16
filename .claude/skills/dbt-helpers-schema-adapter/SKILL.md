---
name: dbt-helpers-schema-adapter
description: Implement and manage dbt YAML schema adapters for bi-directional mapping between dbt versions (e.g., Core 1.10+, Fusion) and the internal IR. Use when adding support for a new dbt version or implementing migration logic.
---

# dbt-helpers-schema-adapter

## Purpose

To decouple the core logic from specific dbt YAML versions and keywords. This allows `dbt-helpers` to support projects using different dbt versions and enables safe migrations.

## Architecture

1. **Normalization**: Parse version-specific YAML (e.g., `tests` in v1) into stable Internal Representation (IR) (e.g., `DbtTestRef`).
2. **Rendering**: Render IR back into version-specific YAML (e.g., `data_tests` in v2).

## Port Definition

The `SchemaAdapter` interface (Protocol) in the SDK requires:

- `parse_model(yaml_node: dict) -> DbtModelRef`
- `render_model(model: DbtModelRef) -> dict`
- (Similar methods for sources, snapshots, etc.)

## Instructions

### When adding support for a new dbt version

1. Create a new plugin in `src/plugins/schemas/`.
2. Implement the `SchemaAdapter` interface for the new version.
3. Register the plugin under the `dbt_helpers.schema_plugins` entry point.

### When implementing migration logic

1. The Core Orchestrator loads the project using the "Source Adapter" (current version).
2. The project state is held as internal IR.
3. The Core Orchestrator saves the project using the "Target Adapter" (new version).

## References

- [ADR 0004: Decoupled dbt Property Version Adapters](../../../docs/adr/0004-decoupled-dbt-property-version-adapters.md)
- [System Design: Handling dbt YAML version drift](../../../docs/core/system_design.md#handling-dbt-yaml-version-drift)
