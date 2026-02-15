# 2. Use Plugin-based Hexagonal Architecture

Date: 2026-02-16

## Status

Accepted

## Context

The `dbt-helpers` project needs to support multiple data warehouses (BigQuery, Snowflake, DuckDB, etc.) and various third-party tools (Lightdash, Elementary, etc.) without becoming tightly coupled to any specific implementation or to `dbt-core` itself. We need a stable core that can orchestrate these integrations safely and efficiently.

## Decision

We will implement a Plugin-based Hexagonal Architecture.

1.  **Core**: Contains the domain logic, orchestrator, and Plan/Diff engine.
2.  **SDK**: Defines the "ports" (interfaces) and "value objects" (IR) that act as the contract between the core and external adapters.
3.  **Plugins (Adapters)**: Implement the ports for specific warehouses and tools.
4.  **Plugin Discovery**: Uses Python entry points for decoupled discovery.
5.  **Control Plane**: The Plugin SDK contracts serve as the control plane for the entire project.

## Consequences

- **Stability**: The SDK provides a stable interface that minimizes breaking changes for plugin authors.
- **Extensibility**: Adding support for new warehouses or tools only requires implementing a new plugin.
- **Safety**: The core can enforce safety boundaries (e.g., restricted metadata access) through the SDK interfaces.
- **Testing**: We can use contract tests in the SDK to ensure plugin compliance.
- **Complexity**: Requires careful management of the SDK versioning and clear documentation of the IR types.
