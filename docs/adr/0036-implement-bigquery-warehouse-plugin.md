# 36. Implement BigQuery Warehouse Plugin

Date: 2026-02-17

## Status

Accepted

## Context

With the Plan/Apply safety workflow finalized in ADR 0034 and authentication patterns defined in ADR 0022, we need to implement the `dbt_helpers_wh_bigquery` warehouse plugin to extend `dbt-helpers` beyond local DuckDB to cloud-scale warehouses. BigQuery is the primary candidate due to its complex namespace hierarchy (`project.dataset.table`), rich metadata (partitioning, clustering, policy tags), and broad adoption in the dbt ecosystem.

## Decision

We will implement the `dbt_helpers_wh_bigquery` plugin as a separate package under `src/plugins/warehouses/`.

1. **Package Structure**: Follow the standard warehouse plugin layout with `plugin.py` implementing `CatalogClient` and `auth.py` for credential handling.
2. **Dependencies**: `google-cloud-bigquery`, `google-auth`, `db-dtypes`.
3. **Namespace Mapping**: BigQuery `project.dataset` maps to `CatalogNamespace(parts=[project, dataset])`. Scope items support `dataset` (using config project) or `project.dataset`.
4. **Metadata Extraction**: Map `time_partitioning`, `range_partitioning`, `clustering_fields` to `CatalogRelation.metadata`; `SchemaField.policy_tags` to `CatalogColumn.metadata`.
5. **Authentication**: Support keyfile, ADC, and Service Account Impersonation (ADR 0022). Use `AnonymousCredentials` when `api_endpoint` is set (emulator/testing).
6. **Integration Testing**: Use `ghcr.io/goccy/bigquery-emulator` via Testcontainers for CI without real GCP credentials.

## Consequences

### Positive

- **Validates 3-Part Namespace**: Confirms `PathPolicy` and `resource_mapper` handle `project.dataset.table` correctly.
- **Enables Governance Tools**: Policy tags and partitioning metadata support future Privacy and optimization plugins.
- **CI-Friendly**: Emulator-based tests run without GCP credentials.

### Negative

- **Emulator Limitations**: The goccy emulator may not support all BigQuery features; some behaviors require manual verification against real BigQuery.
- **Dependency Surface**: Adds `google-cloud-bigquery` and transitive deps to the workspace.

### Links

- Amends: [ADR 0022 BigQuery Authentication and Impersonation Support](0022-bigquery-authentication-and-impersonation-support.md)
