# 23. Data Privacy and PII Tagging Tool Plugin

Date: 2026-02-16

## Status

Proposed

## Context

Privacy-aware data engineering is becoming a standard requirement. Organizations need to classify data (Data Inventory) and apply handling standards (e.g., masking, hashing, dropping columns) to create privacy-protected models for consumers like data analysts.

The `dbt-data-privacy` package provides a mature pattern for this using dbt metadata. We want to incorporate this capability into `dbt-helpers` as a first-class **Tool Plugin**.

## Decision

We will implement the `dbt-helpers-tool-privacy` plugin, which will automate the generation of privacy-protected dbt models based on metadata annotations in `schema.yml`.

1. **Metadata Schema**: We will adopt a metadata schema under `meta.data_privacy` within dbt resource definitions:

   ```yaml
   columns:
     - name: user_id
       meta:
         data_privacy:
           level: confidential # e.g., public, internal, confidential, restricted
           policy_tags: ["unique_identifier"]
   ```

2. **Privacy Objective Configuration**: The `dbt_helpers.yml` will define "Data Objectives" and their associated "Data Handling Standards":

   ```yaml
   tools:
     privacy:
       enabled: true
       objectives:
         data_analysis:
           data_handling_standards:
             confidential:
               method: SHA256
               converted_level: internal
             restricted:
               method: DROPPED
   ```

3. **Plan API Integration**:

   - The Tool Plugin will consume the `CatalogRelation` and existing dbt state.
   - It will emit `PlannedOp` (specifically `CreateFile` for new SQL/YAML files) to create "Privacy Protected Models".
   - These models will be generated using Jinja2 templates (leveraging ADR 0021) to apply the specified masking/hashing logic (e.g., `SHA256(CAST(column AS STRING))`).

4. **PII Detection Heuristics**:

   - The tool will include a diagnostic mode to suggest `data_privacy` levels based on column names (regex-based detection for `email`, `phone`, `user_id`, etc.) and data types.

5. **Bi-directional Sync**:
   - Warehouse plugins (like BigQuery) can attach `policy_tags` to the `CatalogRelation` metadata.
   - The Privacy tool can consume these to suggest or enforce dbt-level privacy configurations.

## Consequences

### Positive

- **Automated Compliance**: Reduces the manual effort required to create and maintain privacy-protected views.
- **Centralized Policy**: Handling standards are defined in a single configuration file (`dbt_helpers.yml`).
- **Standardized Implementation**: Leverages proven patterns from `dbt-data-privacy`.

### Negative

- **Implementation Complexity**: SQL generation for different masking methods and handling relationships (joins) is non-trivial.
- **Dependency on Jinja2**: Strictly depends on the template-based generation logic defined in ADR 0021.

### Risks

- **SQL Dialect Differences**: Masking functions (like `SHA256`) differ across warehouses. The plugin must be aware of the target warehouse dialect or delegate function names to the warehouse plugin.
- **YAML Drift**: As privacy-protected models are generated files, we must ensure they are properly synchronized with their source models.
