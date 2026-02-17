# 24. Resource-Oriented Service Decomposition

Date: 2026-02-16

## Status

Accepted

## Context

As the `dbt-helpers` project grows, the `UnifiedDbtSchemaAdapter` and `Orchestrator` classes have become monolithic "God objects". They handle multiple resource types (Sources, Models, Snapshots) and multiple workflows (Sync, Scaffold, Plan Generation) in a single file. This leads to:

- High cognitive load when making changes.
- Brittle tests that are hard to isolate.
- Difficulty in extending the system with new resource types or workflows.

## Decision

We have decomposed the monolithic implementation into resource-specific renderers and workflow-specific services.

1. **Schema Plugin (Renderers)**:

   - Extracted resource-specific logic into a `renderers/` package within the `dbt_helpers_schema_dbt` plugin.
   - `BaseRenderer`: Provides a shared Jinja2 environment.
   - `SourceRenderer`, `ModelRenderer`, `SnapshotRenderer`: Specialized renderers for each dbt resource type.
   - `UnifiedDbtSchemaAdapter`: Now acts as a facade that delegates to these specialized renderers.

2. **Core Orchestrator (Workflows)**:
   - Extracted workflow logic into a `workflows/` package within the `dbt_helpers_core` package.
   - `SourceSyncService`, `ModelScaffoldService`, `SnapshotScaffoldService`: Specialized service objects that manage the lifecycle of specific workflows.
   - `ResourceMapper`: Centralized the mapping logic from Warehouse Catalog to dbt Intermediate Representation (IR).
   - `Orchestrator`: Now acts as a high-level coordinator that delegates to these service objects.

## Consequences

### Positive

- **Improved Modularity**: Concerns are clearly separated by resource type and workflow.
- **Scalability**: Adding a new resource type (e.g., Seeds) or a new workflow is as simple as creating a new renderer/service.
- **Enhanced Testability**: Unit tests are now isolated to specific renderers and services, making them faster and easier to maintain.
- **Lower Cognitive Load**: Developers can focus on a single module without being overwhelmed by unrelated logic.

### Negative

- **Increased File Count**: Logic is spread across more files, which may require slightly more navigation initially.
- **Indirection**: The facade pattern adds a layer of indirection, though it preserves the existing public API.
