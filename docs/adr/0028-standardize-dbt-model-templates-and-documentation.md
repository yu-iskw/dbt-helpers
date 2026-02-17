# 28. Standardize dbt Model Templates and Documentation

Date: 2026-02-16

## Status

Proposed

## Context

The current dbt model generation templates (`model.sql.j2`, `model.yml.j2`) are minimal and do not enforce engineering best practices or governance standards. Specifically:

- Files lack "Do Not Edit" warnings for generated artifacts.
- Ownership and PII information is not standardized.
- Configuration is hardcoded rather than using dbt variables (e.g., project aliases).
- Documentation is embedded in YAML rather than separated into `doc()` blocks, cluttering the configuration.
- Integration with tools like Lightdash (group labels, labels) is missing.

## Decision

We will adopt a standardized set of Jinja2 templates for dbt resource generation that enforces the following patterns:

1.  **Generated File Warnings**: All generated files will include a header warning developers not to edit them directly.
2.  **Dynamic Configuration**: Use `var('projects')` for project/database mapping instead of hardcoded strings.
3.  **Governance Metadata**:
    - **Owner**: Explicitly defined in `config` and `labels`.
    - **PII**: Explicit `contains_pii` label (defaulting to `false`).
    - **Tags**: Automatic propagation of tags.
4.  **Separated Documentation**:
    - Model descriptions will use `{{ doc("model_name") }}` referencing a separate documentation block.
    - A new template for documentation files (`model_doc.md.j2`) will be introduced.
5.  **Tool Integration**:
    - Include Lightdash-specific meta fields (`group_label`, `label`).
    - Include placeholder tests (`unique`, `not_null`) for standard columns.

The `DbtResourceIR` and `ModelRenderer` will be updated to support passing these specific context variables (`owner`, `project_alias`, `dataset`, `table`, `dbt_helper_version`) to the templates. The `ProjectConfig` will be extended to include `owner` and `project_alias_map` to support this logic.

## Consequences

### Positive

- **Standardization**: All generated models will follow a consistent, high-quality structure.
- **Maintainability**: Clear separation of documentation and configuration.
- **Observability**: Better labeling for ownership and PII status in the data warehouse.
- **Safety**: Reduced risk of accidental edits to generated files.

### Negative

- **Migration**: Existing generated models may need to be regenerated to match the new format.
- **Complexity**: The templates are more complex and require specific metadata to be present in the source IR or config to render correctly.
