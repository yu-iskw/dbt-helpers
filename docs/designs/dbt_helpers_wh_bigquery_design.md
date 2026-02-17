# Design: BigQuery Warehouse Plugin (`dbt_helpers_wh_bigquery`)

## 1. Overview

This document outlines the design for the BigQuery warehouse plugin for `dbt-helpers`.
The plugin implements the `CatalogClient` interface to read metadata from Google BigQuery, supporting advanced features like partitioning, clustering, and Service Account impersonation.

## 2. Dependencies

The plugin requires the following dependencies:

- `dbt-helpers-sdk`: Core SDK.
- `google-cloud-bigquery`: Official BigQuery client.
- `google-auth`: For authentication and impersonation.
- `db-dtypes`: Recommended for BigQuery data type handling.

Dev/Test dependencies:

- `dbt-bigquery`: For integration tests.
- `testcontainers`: For spinning up the BigQuery emulator.
- `pytest`: For running tests.

## 3. Configuration

The plugin will accept a `connection_config` dictionary in `read_catalog`. This configuration mirrors standard BigQuery connection parameters.

### Supported Parameters

| Parameter                     | Type        | Description                                            |
| :---------------------------- | :---------- | :----------------------------------------------------- |
| `project`                     | `str`       | Default GCP project ID.                                |
| `location`                    | `str`       | BigQuery location (e.g., `US`, `EU`).                  |
| `method`                      | `str`       | Auth method: `service-account`, `oauth`, or `default`. |
| `keyfile`                     | `str`       | Path to Service Account JSON keyfile.                  |
| `impersonate_service_account` | `str`       | Email of SA to impersonate.                            |
| `scopes`                      | `list[str]` | OAuth scopes (optional).                               |
| `api_endpoint`                | `str`       | **Testing only**: URL for BigQuery emulator.           |

## 4. Namespace Mapping

BigQuery follows a `Project.Dataset.Table` hierarchy.

- **Scope**: The `scope` argument in `read_catalog` will be interpreted as a list of **dataset IDs**.
  - If an item contains a dot (e.g., `other_project.dataset`), it is treated as `project.dataset`.
  - Otherwise, the configured `project` is prepended.
- **CatalogNamespace**: Maps to `CatalogNamespace(parts=[project, dataset])`.

## 5. Metadata Extraction

We will map specific BigQuery table properties to `CatalogRelation.metadata`.

| BigQuery Property      | Metadata Key                  | Description                                        |
| :--------------------- | :---------------------------- | :------------------------------------------------- |
| `description`          | `description`                 | Table description.                                 |
| `labels`               | `labels`                      | Dictionary of labels.                              |
| `time_partitioning`    | `partitioning`                | Dict with `type`, `field`, `expiration_ms`.        |
| `range_partitioning`   | `partitioning`                | Dict with `field`, `range` (start, end, interval). |
| `clustering_fields`    | `clustering`                  | List of column names.                              |
| `schema[].policy_tags` | `column.metadata.policy_tags` | List of policy tag resource names.                 |

## 6. Authentication Implementation

The authentication logic handles:

1. **Direct Credentials**: Via keyfile or ADC.
2. **Impersonation**: Chaining credentials to assume a target Service Account.

```python
from google.auth import default, load_credentials_from_file
from google.auth.impersonated_credentials import Credentials as ImpersonatedCredentials
from google.cloud import bigquery
from google.oauth2 import service_account

def get_credentials(config: dict):
    creds = None
    if config.get("keyfile"):
        creds = service_account.Credentials.from_service_account_file(
            config["keyfile"],
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
    else:
        creds, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

    # Handle Impersonation
    if config.get("impersonate_service_account"):
        creds = ImpersonatedCredentials(
            source_credentials=creds,
            target_principal=config["impersonate_service_account"],
            target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
            lifetime=3600
        )
    return creds

def get_client(config: dict):
    creds = get_credentials(config)
    client_options = {}
    if config.get("api_endpoint"):
         client_options = {"api_endpoint": config["api_endpoint"]}

    return bigquery.Client(
        project=config.get("project"),
        credentials=creds,
        client_options=client_options
    )
```

## 7. Testing Strategy

We will use a **Nullable Infrastructure** approach combined with **Testcontainers**.

### Unit Tests

- Use `unittest.mock` to mock `google.cloud.bigquery.Client`.
- Verify that `read_catalog` correctly transforms `bigquery.Table` objects into `CatalogRelation` objects.
- Verify that auth logic (impersonation) is called correctly.

### Integration Tests

- **Tool**: `testcontainers-python` with `ghcr.io/goccy/bigquery-emulator`.
- **Setup**:
  1. Spin up the emulator container.
  2. Configure `dbt-bigquery` profile to use `api_endpoint` pointing to the emulator.
  3. Run `dbt build` to seed data (using `dbt_helpers_sdk.testing.DbtRunner`).
  4. Run `BigQueryPlugin.read_catalog` pointing to the emulator.
  5. Assert that returned `CatalogRelation`s match the dbt models.

This ensures we test the full flow without needing real GCP credentials in CI.

## 8. Implementation Plan

1. **Scaffold**: Create `src/plugins/warehouses/dbt_helpers_wh_bigquery`.
2. **Dependencies**: Add `google-cloud-bigquery` and `google-auth` to `pyproject.toml`.
3. **Core Logic**: Implement `plugin.py` with Auth and Metadata extraction.
4. **Unit Tests**: Implement `tests/unit/test_plugin.py`.
5. **Integration**: Implement `tests/integration/` with `testcontainers` and emulator.
