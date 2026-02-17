# 5. Catalog Metadata Extension

Date: 2026-02-16

## Status

Accepted

## Context

Tool plugins (e.g., Lightdash) often require warehouse-specific details that are not part of the core typed Catalog IR. For example:

- BigQuery supports partitioned tables and can require a partition filter.
- Lightdash can use this information to automatically set up "default filters" for its tables.

Currently, the `CatalogRelation` and `CatalogColumn` structures in the `dbt_helpers_sdk` are strictly typed with common fields (name, type, etc.). Adding every warehouse-specific property to the core IR would lead to a bloated and unstable SDK.

We need a way for Warehouse plugins to pass specific details to Tool plugins via the core orchestrator without tightly coupling the plugins or the core.

## Decision

We will add a `metadata: Dict[str, Any]` field to both `CatalogRelation` and `CatalogColumn` in the SDK.

1. **Extensible Metadata**: The `metadata` field allows plugins to attach arbitrary data to catalog objects.
2. **Namespacing**: To prevent key collisions, plugins should use namespaced keys (e.g., `bigquery.partition_info` or `lightdash.display_name`).
3. **Producer/Consumer Pattern**:
   - **Warehouse Plugins (Producers)**: Extract warehouse-specific properties during catalog discovery and populate the `metadata` field.
   - **Tool Plugins (Consumers)**: Check for relevant metadata keys and use them to enhance their generated configurations or operations.
4. **SDK Stability**: The core IR remains stable while allowing for rich, plugin-specific data exchange.

## Consequences

- **Flexibility**: Plugins can collaborate on warehouse-specific features without core SDK changes.
- **Loose Coupling**: Tool plugins can optionally support warehouse-specific features if the metadata is present.
- **Typing Trade-off**: Metadata is not strictly typed in the SDK, shifting the responsibility for validation and documentation to the participating plugins.
- **Discovery**: It becomes easier to implement features like "automatically fill in Lightdash default filters based on BigQuery partition requirements".
