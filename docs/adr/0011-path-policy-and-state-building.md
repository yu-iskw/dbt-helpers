# 11. Path Policy and State Building

Date: 2026-02-16

## Status

Accepted

## Context

The initial MVP implementation of `dbt-helpers` hardcoded file paths (e.g., always writing to `models/sources.yml`). This approach fails for real-world dbt projects where:

1. **Diverse Project Structures**: Different teams organize their models differently (e.g., `models/staging/`, `models/marts/`, or warehouse-specific paths like `models/{{ project }}/{{ dataset }}/`).
2. **Existing Resources**: The tool needs to know where resources already exist to avoid creating duplicates or overwriting unrelated files.
3. **Idempotency**: Running the tool multiple times should produce an empty plan if nothing has changed.

## Decision

We will implement two complementary subsystems:

1. **PathPolicy**: A configurable templating engine that resolves file paths using regex-based variable substitution (e.g., `models/{{ schema }}/{{ table }}.sql`).

   - Variables are extracted from `CatalogRelation` objects (e.g., `schema`, `table`, `project`, `dataset`).
   - Default templates are provided per warehouse type, but users can override them in `dbt_helpers.yml`.
   - Uses simple regex substitution to avoid heavy dependencies like Jinja2.

2. **StateBuilder**: A service that crawls the local filesystem to index existing dbt resources.

   - Scans `models/` directory recursively for `.sql` and `.yml` files.
   - Parses YAML files to extract source and model definitions.
   - Builds a `ProjectState` map: `resource_id -> file_path`.

3. **Orchestrator Integration**: The `Orchestrator` uses both components to make intelligent decisions:
   - If a resource exists in `ProjectState` → Generate `UpdateYamlFile` targeting that specific file.
   - If a resource is new → Use `PathPolicy` to determine the target path and generate `CreateFile`.

## Consequences

- **Flexibility**: Users can customize file organization via `dbt_helpers.yml` paths configuration.
- **Idempotency**: The tool can detect existing resources and avoid duplicate file creation.
- **Safety**: Reduces risk of overwriting unrelated files by targeting the correct existing file.
- **Complexity**: Requires maintaining parsing logic for dbt YAML structures, which may need updates as dbt evolves.
- **Performance**: State building requires filesystem crawling, which may be slow for very large projects (mitigated by caching in future iterations).
