# 27. Standardized YAML config: Block for dbt Resources

Date: 2026-02-16

## Status

Accepted

## Context

Generated dbt schema YAML (sources, models, snapshots) should expose a consistent configuration block so that enabled state, full_refresh behavior, and environment-specific database are set in a uniform way. Without this, generated YAML can omit important config or use inconsistent structure across resource types.

We do not manage de-duplication between the SQL `config()` macro and schema YAML; both may specify config and dbt merges them (see ADR 0026 for SQL).

## Decision

We standardize a `config:` block in all generated source, model, and snapshot YAML templates.

1. **MUST properties (always present in config)**:

   - `enabled: true`
   - `full_refresh: none`

2. **Optional in config**:

   - `database`: When provided (e.g. from workflow using the ADR 0018 pattern), emit `database: "<pattern>"` inside the same `config:` block so environment switching is consistent (see [ADR 0018](0018-standardize-env-switching-with-dbt-vars.md)).

3. **Resource-specific**:

   - **Sources**: config at source level; fusion vs legacy (1.10/1.11) branches both get the MUST props; legacy may also have per-table config where applicable.
   - **Models**: config per model with MUST props and optional database.
   - **Snapshots**: config per snapshot with MUST props and optional database; other snapshot-specific options remain in schema as needed.

4. **Implementation**: Templates in the schema plugin (`dbt_helpers_schema_dbt`) are updated so that source.yml.j2, model.yml.j2, and snapshot.yml.j2 always emit a `config:` block with the MUST properties and optional database. Workflows (SourceSyncService, ModelScaffoldService, SnapshotScaffoldService) build the database pattern and pass it into the schema adapter’s render methods.

## Consequences

- All generated YAML has a predictable config shape and works with dbt’s merging of config from SQL and YAML.
- Environment switching (ADR 0018) is supported for sources, models, and snapshots when the workflow supplies the database pattern.
- Consistency across resource types simplifies tooling and user expectations.
