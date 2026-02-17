# 26. Standardized SQL config() Macro for dbt Resources

Date: 2026-02-16

## Status

Accepted

## Context

Generated dbt model and snapshot SQL files need a consistent, robust configuration block. The dbt `config()` macro controls materialization, refresh behavior, and environment-specific settings. Without standardizing which properties we set and how, generated files can be incomplete or diverge from dbt best practices.

We do not attempt to de-duplicate or reconcile configuration between the SQL `config()` block and schema YAML; both may contain config and dbt merges them (see ADR 0027 for YAML).

## Decision

We standardize the SQL `config()` macro in all generated model and snapshot SQL templates.

1. **MUST properties (always set)**:

   - `enabled=true`
   - `full_refresh=none`
   - `materialized` (models only; from resource config or default `view`)
   - `alias` (resource name)

2. **Optional but standardized when present**:

   - `database`: When provided, use the ADR 0018 pattern so environment switching works (see [ADR 0018](0018-standardize-env-switching-with-dbt-vars.md)). The template receives a pre-built Jinja string; we strip stray `{{`/`}}` only for safe embedding inside the macro.
   - `tags`, `labels` (from resource): Rendered via `tojson` where applicable.

3. **Snapshot-specific**: Snapshot SQL additionally includes a config dict (e.g. `unique_key`, `strategy`, `target_schema`) passed from the scaffold workflow; values are rendered with `tojson` in the template loop.

4. **Implementation**: Templates live in the schema plugin (`dbt_helpers_schema_dbt`). Model and snapshot renderers pass `database` when the workflow provides it (e.g. ModelScaffoldService, SnapshotScaffoldService build the pattern and pass it to `render_model_sql` / `render_snapshot_sql`).

## Consequences

- Generated SQL is predictable and aligns with dbt’s expected config shape.
- Environment switching (ADR 0018) applies to both models and snapshots when workflows pass the database pattern.
- No custom dbt macros are required; we only set standard config keys in Jinja-generated SQL.
