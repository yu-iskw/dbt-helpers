# 22. BigQuery Authentication and Impersonation Support

Date: 2026-02-16

## Status

Proposed

## Context

The `dbt-helpers` project aims to provide a secure and enterprise-ready way to manage dbt projects. For Google Cloud BigQuery, the default authentication (using Application Default Credentials) is often insufficient in complex environments where users need to impersonate service accounts for better auditing and least-privilege access.

The legacy architecture and past implementations showed a need for:

- Support for Service Account impersonation.
- Configurable OAuth scopes.
- Quota project management.
- Integration with the `google-auth` library lifecycle.

Currently, the `dbt-helpers-wh-bigquery` plugin (planned/scaffolded) needs a standardized way to handle these authentication requirements without hardcoding them into the core orchestrator.

## Decision

We will implement a robust authentication layer within the `dbt-helpers-wh-bigquery` plugin that supports service account impersonation and advanced configuration.

1. **Configuration Schema**: The `dbt_helpers.yml` file will support an `auth` section within the warehouse connection configuration:

   ```yaml
   warehouse:
     plugin: "bigquery"
     connection:
       project_id: "my-project"
       location: "US"
       auth:
         impersonate_service_account: "dbt-runner@my-project.iam.gserviceaccount.com"
         quota_project_id: "my-quota-project"
         scopes:
           - "https://www.googleapis.com/auth/bigquery"
           - "https://www.googleapis.com/auth/cloud-platform"
         lifetime: 3600
   ```

2. **Plugin Implementation**: The BigQuery plugin will use the `google-auth` library to handle credential acquisition. If `impersonate_service_account` is provided, it will use `impersonated_credentials.Credentials` to wrap the source credentials.

3. **SDK Alignment**: The `CatalogClient` interface in the SDK will continue to receive the `connection_config` as a dictionary, allowing plugins to extract their specific auth needs without the SDK needing to know about BigQuery-specific details.

4. **Security Best Practices**:
   - Avoid storing secrets in `dbt_helpers.yml`. Use environment variable expansion (already supported by the orchestrator).
   - Default to standard Application Default Credentials if no `auth` section is provided.

## Consequences

### Positive

- **Enterprise Readiness**: Supports common security patterns used in large organizations.
- **Improved Auditing**: Impersonation provides a clear audit trail of who performed which action.
- **Flexibility**: Allows users to override scopes and quota projects as needed.

### Negative

- **Complexity**: The authentication logic in the plugin becomes more complex.
- **Dependency**: The BigQuery plugin will have a firm dependency on `google-auth`.

### Risks

- **Credential Lifetime**: Long-running operations might exceed the default impersonation lifetime (default 3600s). We will allow this to be configurable.
- **Permission Errors**: Misconfiguration of IAM roles (e.g., missing `Service Account Token Creator`) can lead to confusing errors. We should provide clear diagnostics if impersonation fails.
