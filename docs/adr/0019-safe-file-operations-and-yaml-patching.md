# 19. Safe File Operations and YAML Patching Strategy

Date: 2026-02-16

## Status

Accepted

## Context

The current implementation of `dbt-helpers` focuses on generating a "Plan" that describes intended file changes, but it lacks a safe and standardized mechanism to "Apply" that plan. To fulfill the project's goal of being a production-ready toolkit, we need a robust I/O layer that ensures:

1. **Safety**: No partial or corrupted file writes.
2. **Idempotency**: Repeatedly applying the same plan should result in no further changes.
3. **Auditability**: Every change must be recorded for governance and debugging.
4. **Preservation**: Manual edits and comments in existing dbt YAML files must be preserved during updates.

## Decision

We will implement a two-layered "Apply" mechanism consisting of a `YamlStore` for high-level YAML manipulation and a `SafeFSWriter` for low-level atomic file operations.

### 1. YamlStore (Preservation Layer)

- We will use `ruamel.yaml` as the underlying engine because it excels at preserving comments, document order, and literal block styles.
- The `YamlStore` will provide a set of patch operations (e.g., `EnsureMappingKey`, `MergeSequenceUnique`) to modify dbt resources in a non-destructive manner.

### 2. SafeFSWriter (Safety & Audit Layer)

- **Atomic Writes**: Files will be written to a temporary location (e.g., `.filename.sql.tmp`) on the same filesystem and then moved to the final destination using `os.replace`. This ensures that even in the event of a crash or power failure, files are either fully written or not at all.
- **Automated Backups**: Before modifying any existing file, a compressed backup will be stored in `.dbt_helpers/backups/` indexed by timestamp and path.
- **Audit Logging**: All operations (Create, Update, Delete) will be recorded in a JSONL formatted audit log at `.dbt_helpers/audit.jsonl`, including metadata like timestamp, operation kind, and file hash.

### 3. Orchestration

- The `Orchestrator` will bridge the `Plan` and the `SafeFSWriter`.
- For `UpdateYamlFile` operations, the `Orchestrator` will use `YamlStore` to load the current content, apply the patches, and then pass the resulting string to the `SafeFSWriter` for an atomic update.

## Consequences

### Positive

- **High Reliability**: Users can trust the tool with their primary dbt project files.
- **Improved UX**: Non-destructive YAML editing means users can continue to use the tool alongside manual edits without fear of losing comments.
- **Governance**: Audit logs provide a clear trail of what the tool changed and when.

### Negative

- **Complexity**: Implementing atomic swaps and backup management adds overhead to the core logic.
- **Performance**: Double-writing files (temp then rename) and generating backups increases I/O latency, though this is negligible for typical dbt project sizes.
- **Dependency**: Adds a hard dependency on `ruamel.yaml` in `dbt_helpers_core`.
