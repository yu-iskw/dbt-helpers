# 21. Use Jinja2 for dbt Resource Generation

Date: 2026-02-16

## Status

Proposed

## Context

Currently, `dbt-helpers` generates dbt YAML and SQL files through a mix of manual dictionary construction (for YAML) and hardcoded f-strings (for SQL).

- **Hardcoded Logic**: The SQL generation logic for models is currently embedded within `Orchestrator.scaffold_models`, violating the separation of concerns where the schema plugin should own the dbt-specific syntax.
- **Limited Customizability**: Users cannot easily modify the output format without changing the core code.
- **Maintenance Overhead**: As dbt syntax evolves or users request different styles (e.g., specific header comments, different YAML structures), maintaining hardcoded strings becomes cumbersome.
- **Inconsistency**: YAML generation uses `yaml.dump` which is safe but rigid, while SQL uses f-strings which are flexible but prone to errors if not carefully managed.

## Decision

We will adopt **Jinja2** as the standard templating engine for generating all dbt resources (Sources, Models, Snapshots) within the `dbt-helpers-schema-dbt` plugin.

1. **Add Jinja2 Dependency**: Add `jinja2` to `dbt-helpers-sdk` so it is available to all plugins.
2. **Template-Based Generation**: Move all generation logic to Jinja2 templates (`.j2`) located within the schema plugin.
   - `source.yml.j2`
   - `model.yml.j2`
   - `model.sql.j2`
   - `snapshot.yml.j2`
   - `snapshot.sql.j2`
3. **Update SchemaAdapter Interface**: Expand the `SchemaAdapter` protocol in the SDK to include `render_model_sql`. This allows the Orchestrator to delegate SQL generation to the plugin, which will use the `model.sql.j2` template.
4. **Refactor Adapter**: The `UnifiedDbtSchemaAdapter` will initialize a Jinja2 environment and use it to render these templates.

## Consequences

### Positive

- **Separation of Concerns**: The Orchestrator no longer knows about dbt SQL syntax; it just provides the Intermediate Representation (IR).
- **Customizability**: In the future, we can allow users to provide their own templates directory to override the defaults.
- **Readability**: Templates are easier to read and understand than Python code constructing strings or dictionaries.
- **Consistency**: All generation follows the same pattern.

### Negative

- **New Dependency**: Adds `jinja2` to the project dependency tree.
- **Complexity**: Loading and rendering templates adds a slight overhead compared to f-strings.
- **YAML Strictness**: Generating YAML via templates requires care to ensure valid indentation and syntax, whereas `yaml.dump` guarantees validity. We will mitigate this by ensuring templates are well-tested and potentially validating the output with `yaml.safe_load` in tests.

### Risks

- **Whitespace Control**: Jinja2 whitespace control can be tricky in YAML. We will adopt the following policy:
  - Use `{%-` and `-%}` for all control structures (if, for, set) to minimize unintended blank lines.
  - Configure the Jinja2 environment with `trim_blocks=True` and `lstrip_blocks=True` for predictability.
  - Use the `indent` filter for multi-line content (like nested YAML blocks) to ensure correct YAML indentation.
