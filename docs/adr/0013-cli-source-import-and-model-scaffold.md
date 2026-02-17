# 13. CLI Command Structure: Source Import and Model Scaffold

Date: 2026-02-16

## Status

Accepted

## Context

The current `dbt-helpers-cli` implementation has a single top-level command `source-generate` that handles source generation. As we expand the tool's capabilities to include model scaffolding and other management tasks, a flat command structure will become difficult to organize and discover. Additionally, we need to support generating dbt models (SQL and YAML) based on warehouse metadata, which requires extending the core orchestration and schema adapter logic.

## Decision

We will restructure the CLI to use a hierarchical command group pattern and implement new core capabilities:

1. **Hierarchical CLI Groups**:

   - `dbth source`: Group for source management.
     - `import`: Renamed from `generate`. Reads warehouse catalog and proposes source YAML.
   - `dbth model`: Group for model management.
     - `scaffold`: Reads warehouse catalog for specified tables and generates staging model SQL (with `{{ source() }}`) and YAML properties.

2. **Core Extensions for Model Generation**:

   - Update `ProjectConfig` to include a default path for model YAML files.
   - Extend `SchemaAdapter` protocol to support `render_model_yaml`.
   - Implement `Orchestrator.scaffold_models` to orchestrate catalog reading, path resolution, and multi-file (SQL/YAML) plan generation.

3. **DuckDB Plugin Enhancement**:
   - Optimize `read_catalog` for performance (bulk fetching).
   - Ensure the plugin is robustly tested for these new commands.

## Consequences

- **Improved CLI UX**: Grouping commands by resource type (`source`, `model`) provides a more intuitive interface consistent with other modern CLI tools (like `git` or `kubectl`).
- **Accelerated Development**: `model scaffold` significantly reduces manual effort in creating staging layers for new dbt projects.
- **Extensibility**: The structured CLI groups make it easier to add future commands like `test generate` or `docs audit`.
- **Standardized Scaffolding**: Core-level scaffolding ensures consistent SQL patterns (e.g., base CTEs) across the project.
