# 25. IR-Centric Resource Management

Date: 2026-02-16

## Status

Accepted

## Context

The `dbt-helpers` project currently relies on Tool Plugins (like Lightdash) generating file content directly via `Plan` operations. This creates tight coupling between tools and the dbt YAML structure.

With the release of dbt 1.10, significant changes were introduced to the `meta` and `tags` configuration:

1.  Top-level `meta` and `tags` are deprecated.
2.  All custom metadata must be nested under `config: { meta: ... }`.

This change breaks existing Tool Plugins that assume a specific YAML structure or try to patch top-level keys. Furthermore, supporting multiple dbt versions (legacy vs modern) in every plugin leads to combinatorial complexity and duplication.

## Decision

We will adopt an **IR-Centric Architecture** and drop support for dbt versions 1.9 and older.

1.  **IR as the Single Source of Truth**:

    - The `DbtResourceIR` (Intermediate Representation) will remain the stable contract for all plugins.
    - Tool Plugins will no longer emit raw file patches. Instead, they will emit **Intent** (e.g., `UpdateResource` operations containing partial IR updates).

2.  **Schema Adapter as the Sole Gateway**:

    - The `SchemaAdapter` is the only component allowed to serialize/deserialize YAML.
    - It will enforce dbt 1.10+ standards by _always_ rendering metadata under `config.meta` and tags under `config.tags`.
    - It will be responsible for calculating the precise file patches required to transition a file from its current state to the desired IR state.

3.  **Orchestrator as Mediator**:

    - The Orchestrator will receive high-level intent from tools.
    - It will coordinate the read-modify-write cycle:
      1.  Read existing file.
      2.  Parse into IR via Schema Adapter.
      3.  Apply tool intent to IR.
      4.  Delegate patch calculation to Schema Adapter.
      5.  Apply file patches.

4.  **Drop Support for dbt <= 1.9**:
    - We will not support legacy dbt versions that require top-level `meta`.
    - All generated code and patches will strictly follow modern dbt standards.

## Consequences

### Positive

- **Decoupling**: Tool Plugins are completely isolated from dbt version specifics. They only need to know about the stable IR.
- **Consistency**: All generated YAML will consistently follow dbt 1.10+ best practices (nested config), regardless of which tool generated it.
- **Future-Proofing**: Migrating to dbt 2.0 or other future versions will only require updating the `SchemaAdapter`, not every single tool plugin.
- **Simplified Tool Logic**: Tools no longer need to implement complex YAML patching logic or handle file I/O nuances.

### Negative

- **Loss of Legacy Support**: Users on dbt 1.9 or older will not be able to use the latest version of `dbt-helpers` without upgrading their dbt project structure.
- **Orchestrator Complexity**: The Orchestrator takes on more responsibility for coordinating the read-modify-write cycle, potentially impacting performance (though this is mitigated by the safety and correctness gains).
