# 7. Categorized Plugin Directory Structure

Date: 2026-02-16

## Status

Accepted

## Context

As the number of plugins in the `dbt-helpers` project grows, having all of them in a single `src/plugins` directory makes it difficult to distinguish between different types of plugins (warehouses, tools, schemas). This flat structure reduces discoverability and makes the organization less intuitive.

## Decision

We will reorganize the `src/plugins` directory into subdirectories based on the plugin's primary responsibility:

- `src/plugins/warehouses/`: For warehouse adapters (e.g., BigQuery, DuckDB).
- `src/plugins/tools/`: For tool integrations (e.g., Lightdash, Elementary).
- `src/plugins/schemas/`: For dbt schema version adapters (e.g., dbt Core v2, Fusion).

Existing plugins will be moved into these categories:

- `dbt_helpers_wh_bigquery` -> `src/plugins/warehouses/dbt_helpers_wh_bigquery`
- `dbt_helpers_wh_duckdb` -> `src/plugins/warehouses/dbt_helpers_wh_duckdb`
- `dbt_helpers_tool_lightdash` -> `src/plugins/tools/dbt_helpers_tool_lightdash`
- `dbt_helpers_tool_elementary` -> `src/plugins/tools/dbt_helpers_tool_elementary`
- `dbt_helpers_schema_v2` -> `src/plugins/schemas/dbt_helpers_schema_v2`
- `dbt_helpers_schema_fusion` -> `src/plugins/schemas/dbt_helpers_schema_fusion`

## Consequences

- Improved project organization and discoverability of plugins.
- Clearer separation of concerns within the `plugins` directory.
- Requires updating `pyproject.toml` workspace configuration if it specifically lists these directories.
- Any scripts or CI/CD pipelines relying on the previous flat structure will need to be updated.
