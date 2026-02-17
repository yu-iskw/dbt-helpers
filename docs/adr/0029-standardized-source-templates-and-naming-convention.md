# 29. Standardize dbt Source Templates and Naming Convention

Date: 2026-02-16

## Status

Proposed

## Context

The current dbt source generation creates simple source YAML files that lack support for advanced BigQuery features, standardized naming conventions, and governance metadata (freshness, data privacy).
We need a more robust way to generate sources that:

1. Follows a `project__dataset__table` naming convention for dbt table names to avoid name collisions across datasets.
2. Uses dbt `var('projects')` for database references.
3. Includes standardized placeholders for table descriptions.
4. Supports freshness configuration and metadata labels.
5. Integrates with the `data_privacy` tool.

## Decision

We will adopt a standardized dbt source template and naming convention:

1. **Naming Convention**: dbt table names within a source will follow the pattern `{{ project_alias }}__{{ dataset }}__{{ table_name }}`. The `identifier` will remain the raw table name.
2. **Shared Macros**: Introduce `macros.jinja` to share Jinja logic between templates (e.g., `normalize_project_id`, `generate_reference_id`).
3. **Governance Metadata**:
   - **Freshness**: Default freshness warnings and errors will be included in the generated YAML.
   - **Labels**: Resource metadata will be propagated to BigQuery labels via the `meta.labels` block.
   - **Data Privacy**: Support for `data_privacy` objectives and column-level security levels.
4. **Enriched Context**: The `SourceSyncService` will provide an enriched `context` dictionary to the renderer, including `dbt_helper_version`, `project_alias`, and `dataset`.

## Consequences

### Positive

- **Avoids Collisions**: The naming convention prevents name conflicts when importing tables with the same name from different projects/datasets.
- **Improved Governance**: Freshness and data privacy metadata are included by default.
- **Better Developer Experience**: Standardized descriptions and placeholders provide clear guidance for documentation.

### Negative

- **Incompatibility**: Existing source references using the old naming convention will need to be updated.
- **Template Complexity**: The source YAML template is significantly more complex due to the added macros and metadata blocks.
