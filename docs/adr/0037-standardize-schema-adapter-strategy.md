# 37. Standardize Schema Adapter Strategy

Date: 2026-02-18

## Status

Accepted

## Context

The `dbt-helpers` system is designed to be warehouse-agnostic and support various dbt project structures. However, the current implementation of schema adapter selection in the `Orchestrator` is hardcoded to use a single "dbt" adapter. This limits the tool's ability to support different dbt flavors (e.g., dbt Core, dbt Fusion/SQLMesh) which may have different YAML schemas and resource management requirements.

To fulfill the vision of a pluggable hexagonal architecture, we need a standardized way to discover, select, and use different schema adapters based on project configuration.

## Decision

We will standardize the schema adapter strategy by implementing dynamic discovery and configuration-driven selection.

1.  **Dynamic Discovery**: Schema adapters will be discovered using Python entry points under the namespace `dbt_helpers.schema`.
2.  **Configuration-Driven Selection**: The active schema adapter will be specified in the `dbt_helpers.yml` configuration file under the `dbt_properties.adapter` key.
3.  **Interface Enforcement**: All schema adapters must implement the `SchemaAdapter` Protocol defined in `dbt_helpers_sdk`.
4.  **Plugin Architecture**: Schema adapters will be implemented as independent plugins, allowing for easy extension without modifying the core orchestrator.
5.  **Internal IR Stability**: The core logic and tool plugins will continue to operate on the stable internal Intermediate Representation (IR), with schema adapters acting as the bidirectional translation layer ("Corruption Layer") between IR and version-specific YAML/SQL.

## Consequences

### Positive

- **Extensibility**: New dbt flavors or version-specific schema changes can be supported by simply adding a new plugin.
- **Decoupling**: The core orchestrator is no longer aware of specific dbt schema details, improving maintainability.
- **Flexibility**: Projects can easily switch between dbt Core and Fusion by changing a single configuration value.

### Negative

- **Configuration Overhead**: Users must ensure the correct adapter is specified in their configuration.
- **Plugin Management**: Requires ensuring that the necessary schema plugin packages are installed in the environment.

## Links

- Amends: [ADR 0004 Decoupled dbt Property Version Adapters](0004-decoupled-dbt-property-version-adapters.md)
- Related: [ADR 0025 IR-Centric Resource Management](0025-ir-centric-resource-management.md)
