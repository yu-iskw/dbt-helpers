---
name: dbt-helpers-sdk-contract
description: Manage and enforce dbt-helpers SDK contracts, including IR types (Catalog, Resource) and the Plan API. Use when defining interfaces, adding IR types, or implementing the Plan engine.
---

# dbt-helpers-sdk-contract

## Purpose

This skill ensures that all components of `dbt-helpers` adhere to the stable SDK contracts. The SDK is the control plane that enables Hexagonal Architecture by decoupling the core from plugins.

## SDK Components

### 1. Catalog IR (Warehouse Metadata)

- `CatalogNamespace`: Positional parts (e.g., `["project", "dataset"]`).
- `CatalogRelation`: Namespace + name + kind + metadata.
- `CatalogColumn`: Name, type, nullability, description, tags, constraints + metadata.
- **Metadata Field**: `Dict[str, Any]` for namespaced plugin collaboration (e.g., `bigquery.partition_info`).

### 2. dbt Resource IR

- `DbtModelRef`, `DbtSourceRef`, `DbtSnapshotRef`.
- `DbtYamlDoc`: Wrapper for round-trip YAML manipulation.

### 3. Plan API

- `PlannedOp`: Base class for operations.
- `CreateFile(path, content)`
- `UpdateYamlFile(path, yaml_patch_ops)`
- `DeleteFile(path)`
- `AddDiagnostics(level, message)`

## Instructions

### When defining new IR types

1. Ensure they are serializable and warehouse-agnostic.
2. Add necessary metadata fields for plugin-specific extensions.
3. Update conformance tests in the SDK test harness.

### When implementing Plan operations

1. Ensure idempotency (multiple runs result in empty plan if state is unchanged).
2. Use `UpdateYamlFile` for safe, comment-preserving YAML edits.
3. Validate that `path` is within the project root.

## References

- [System Design: Plugin SDK Contracts](../../../docs/core/system_design.md#plugin-sdk-contracts)
- [ADR 0005: Catalog Metadata Extension](../../../docs/adr/0005-catalog-metadata-extension.md)
- [ADR 0003: Use Plan API for Safe File Operations](../../../docs/adr/0003-use-plan-api-for-safe-file-operations.md)
