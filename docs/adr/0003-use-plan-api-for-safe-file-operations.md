# 3. Use Plan API for Safe File Operations

Date: 2026-02-16

## Status

Accepted

## Context

Modifying dbt project files (SQL and YAML) can be destructive if not handled carefully. We want to provide a way for users to audit proposed changes before they are applied, and ensure that changes are applied atomically and idempotently.

## Decision

We will use a "Plan API" where plugins and core policies propose changes as a set of structured operations (`PlannedOp`), which are then reviewed and applied by the core.

1.  **PlannedOp Types**: `CreateFile`, `UpdateYamlFile`, `DeleteFile`, `AddDiagnostics`.
2.  **Two-Phase Execution**:
    - **Phase 1 (Plan)**: Core generates a summary of changes and diffs for the user to review.
    - **Phase 2 (Apply)**: Core applies the reviewed plan atomically, creating backups and audit logs.
3.  **Restricted IO**: Plugins are forbidden from direct file system access; they must return a list of `PlannedOp` objects.

## Consequences

- **Auditability**: Users can see exactly what will change before it happens using the `--plan` flag.
- **Idempotency**: Repeated runs with the same state will yield an empty plan.
- **Safety**: Reduces the risk of accidental data loss or corrupted YAML files.
- **Ease of Testing**: Core logic can be tested by asserting the generated plan without actually touching the disk.
