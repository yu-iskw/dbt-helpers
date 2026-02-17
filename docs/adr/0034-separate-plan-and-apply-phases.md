# 34. Separate Plan and Apply Phases

Date: 2026-02-17

## Status

Accepted

## Context

The initial implementation of the `dbt-helpers` CLI allowed for immediate application of changes using an inline `--apply` flag. While convenient for quick tasks, this approach presents several risks:

- **Lack of Verification**: Users might apply changes without seeing the full scope of what will be modified.
- **Limited Observability**: There is no easy way to inspect a plan before it is executed, especially in non-interactive environments like CI/CD.
- **Atomic Operations**: It's difficult to separate the "read-only" catalog extraction phase from the "write-heavy" filesystem application phase.
- **Auditability**: Without a serialized plan, it's harder to track exactly what was proposed versus what was executed.

## Decision

We will adopt a two-phase "Plan and Apply" workflow, similar to industry-standard tools like Terraform.

1. **Persistent Plan Serialization**: The `Plan` model in the SDK will be updated to support full JSON serialization and deserialization.
2. **Phase 1: Planning**: Commands like `model scaffold` and `source sync` will generate a plan. Users can save this plan to a file using the `--out <path>` flag.
3. **Rich Visualization**: The `print_plan` utility will be enhanced to show rich diffs (using `difflib`) and syntax-highlighted code blocks for all operations.
4. **Phase 2: Explicit Application**: A new top-level `dbth apply <plan_path>` command will be introduced to execute a saved plan. This command will re-verify the plan and prompt for confirmation (unless overridden).
5. **Deprecation of Inline Apply**: The existing `--apply` flag on generation commands will be marked as deprecated. A warning will be displayed encouraging users to move to the new two-phase workflow.

## Consequences

### Positive

- **Safety**: Users can review exactly what will happen before committing changes to their dbt project.
- **CI/CD Integration**: Plans can be generated in one CI step (e.g., as a PR comment) and applied in another (e.g., after approval).
- **Deterministic Execution**: Applying a saved plan ensures that the execution is based on the exact state captured during the planning phase.
- **Better Debugging**: Saved plans can be shared for troubleshooting without requiring access to the warehouse.

### Negative

- **Workflow Verbosity**: Performing a quick change now requires two commands (or ignoring a warning).
- **Disk Usage**: Serialized plans take up some space (though minimal).
- **Complexity**: Requires managing plan serialization/deserialization and ensuring compatibility across versions.
