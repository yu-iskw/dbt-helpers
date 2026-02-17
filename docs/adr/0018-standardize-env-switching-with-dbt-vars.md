# 18. Standardize Environment Switching with dbt Project Variables

Date: 2026-02-16

## Status

Accepted

## Context

Different data warehouses have different ways of handling environments. For example, BigQuery often uses multiple Google Cloud Projects (staging-project, prod-project) which correspond to the `database` field in dbt. Other warehouses like Postgres might use the same database name but different connections in `profiles.yml`.

We need a consistent way to handle these environment-specific database/project references in the generated dbt scaffolds (sources and models) so that users can easily switch environments without manually editing YAML or SQL files.

Users typically use dbt project variables (`vars`) to manage these mappings, often passing them via `--vars` CLI option.

## Decision

We will standardize on a specific Jinja pattern for the `database` field in generated dbt sources.

The pattern is:
`{{ var('databases', var('projects', {})).get('<source_name>', target.database) }}`

- **Primary variable**: `databases` (following dbt best practices for database mappings).
- **Secondary variable (alias)**: `projects` (commonly used in BigQuery contexts).
- **Fallback**: `target.database` (ensures the project continues to work even if no variables are provided, using the connection's default database).

### Implementation Details

1. **Schema Adapter Interface**: The `SchemaAdapter`'s `render_source_yaml` method is updated to accept `source_name` and an optional `database` string.
2. **Unified Dbt Schema Adapter**: The implementation now correctly renders the `database` field at the source level if provided.
3. **Orchestrator Logic**: When generating a source plan, the `Orchestrator` automatically constructs the environment switching Jinja pattern using the source name extracted from the warehouse metadata.

## Consequences

### Positive

- **Flexibility**: Users can switch entire sets of projects/databases by simply changing the `vars` passed to dbt.
- **Robustness**: The fallback to `target.database` ensures that local development or simpler single-database setups work without extra configuration.
- **Consistency**: All generated sources follow the same pattern, making the project structure predictable.
- **BigQuery First-Class Support**: The inclusion of the `projects` alias makes it natural for GCP users.

### Negative

- **Verbosity**: The Jinja string in the YAML file is longer and slightly more complex to read for beginners.
- **Dependency on `vars`**: Encourages a specific way of managing variables which might differ from some users' existing patterns (though the fallback helps).
