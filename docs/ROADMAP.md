# dbt-helpers Roadmap

This document outlines the development priorities and future direction of the `dbt-helpers` project.

## 🎯 Immediate Priorities

### 1. BigQuery Authentication & Impersonation Support

- **Goal**: Secure, enterprise-grade authentication for BigQuery.
- **Key Features**:
  - Service Account impersonation.
  - Custom OAuth scopes and quota project configuration.
  - Hardened audit trail for automated operations.
- **Reference**: [ADR 0022](../docs/adr/0022-bigquery-authentication-and-impersonation-support.md)

### 2. Data Privacy & PII Tagging Tool Plugin

- **Goal**: Automated generation of privacy-protected dbt models.
- **Key Features**:
  - Metadata-driven classification (`meta.data_privacy`).
  - Automated hashing (SHA256) and column dropping.
  - PII detection heuristics for column tagging suggestions.
- **Reference**: [ADR 0023](../docs/adr/0023-data-privacy-and-pii-tagging-tool-plugin.md)

### 3. Template-Based Generation (Jinja2)

- **Goal**: Standardize dbt resource generation across all plugins.
- **Key Features**:
  - Move from f-strings to `.j2` templates.
  - Allow user-defined template overrides for custom SQL/YAML styles.
- **Reference**: [ADR 0021](../docs/adr/0021-use-jinja2-for-dbt-resource-generation.md)

---

## 🛠️ Mid-Term Backlog

### Bi-Directional Metadata Sync

- **Description**: Port dbt descriptions and tags _back_ to warehouse datasets (e.g., BigQuery labels).
- **Status**: Proposed.

### Advanced Column Type Reconciliation

- **Description**: Smart diffing for YAML updates that preserves manual documentation even if column types evolve.
- **Status**: Proposed.

### Manifest-Based State Hydration

- **Description**: Optimize performance by reading `manifest.json` instead of parsing individual YAML files.
- **Status**: Performance Optimization.

---

## 🚀 Future Vision

- **Warehouse Adapters**: Expand support to Snowflake, Redshift, and Databricks.
- **Tool Ecosystem**: Native plugins for Elementary, Lightdash, and Monte Carlo.
- **CLI UX**: Dynamic shell completion and project health-check commands.
