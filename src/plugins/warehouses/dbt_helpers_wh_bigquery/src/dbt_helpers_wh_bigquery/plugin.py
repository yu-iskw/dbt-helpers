"""BigQuery warehouse plugin implementing CatalogClient."""

from typing import Any

from google.api_core.client_options import ClientOptions
from google.auth.credentials import AnonymousCredentials
from google.cloud import bigquery

from dbt_helpers_sdk import (
    CatalogClient,
    CatalogColumn,
    CatalogNamespace,
    CatalogRelation,
)

from .auth import get_credentials


def _parse_scope_item(item: str, default_project: str | None) -> tuple[str, str]:
    """Parse a scope item into (project, dataset).

    If item contains a dot (e.g. 'other_project.dataset'), treat as project.dataset.
    Otherwise, use default_project and item as dataset.
    """
    if "." in item:
        parts = item.split(".", 1)
        return parts[0], parts[1]
    if default_project:
        return default_project, item
    raise ValueError(f"Cannot resolve scope '{item}': no project specified and item has no dot")


# SDK field_type to standard SQL type name mapping
_FIELD_TYPE_TO_SQL: dict[str, str] = {
    "INTEGER": "INT64",
    "FLOAT": "FLOAT64",
    "BOOLEAN": "BOOL",
    "RECORD": "STRUCT",
}


def _map_to_sql_type(field: Any) -> str:
    """Reconstruct the full BigQuery SQL type string from a SchemaField."""
    raw_type = field.field_type or "STRING"
    base_type = _FIELD_TYPE_TO_SQL.get(raw_type, raw_type)

    # Handle parameterized types
    if base_type == "STRING" and getattr(field, "max_length", None):
        base_type = f"STRING({field.max_length})"
    elif base_type == "BYTES" and getattr(field, "max_length", None):
        base_type = f"BYTES({field.max_length})"
    elif base_type in ("NUMERIC", "BIGNUMERIC") and getattr(field, "precision", None):
        scale = getattr(field, "scale", None)
        if scale is not None:
            base_type = f"{base_type}({field.precision}, {scale})"
        else:
            base_type = f"{base_type}({field.precision})"

    # Handle STRUCT (RECORD)
    if base_type == "STRUCT":
        sub_fields = getattr(field, "fields", None) or []
        inner = ", ".join(f"{f.name} {_map_to_sql_type(f)}" for f in sub_fields)
        base_type = f"STRUCT<{inner}>"

    # Handle RANGE
    if base_type == "RANGE":
        range_elem = getattr(field, "range_element_type", None)
        elem_type = getattr(range_elem, "element_type", "UNKNOWN") if range_elem else "UNKNOWN"
        base_type = f"RANGE<{elem_type}>"

    # Handle ARRAY (REPEATED mode)
    if getattr(field, "mode", None) == "REPEATED":
        return f"ARRAY<{base_type}>"
    return base_type


def _map_schema_field(field: Any) -> CatalogColumn:
    """Map a BigQuery SchemaField to CatalogColumn."""
    metadata: dict[str, Any] = {}
    if hasattr(field, "policy_tags") and field.policy_tags:
        names = getattr(field.policy_tags, "names", None) or []
        metadata["policy_tags"] = list(names)
    return CatalogColumn(
        name=field.name,
        data_type=_map_to_sql_type(field),
        description=field.description or None,
        nullable=field.mode != "REQUIRED" if field.mode else True,
        metadata=metadata,
    )


def _extract_partitioning(table: Any) -> dict[str, Any] | None:
    """Extract partitioning info from a BigQuery Table."""
    if table.time_partitioning:
        tp = table.time_partitioning
        return {
            "type": "time",
            "field": getattr(tp, "field", None),
            "expiration_ms": getattr(tp, "expiration_ms", None),
        }
    if table.range_partitioning:
        rp = table.range_partitioning
        range_obj = getattr(rp, "range_", None)
        range_dict: dict[str, Any] = {}
        if range_obj:
            range_dict["start"] = getattr(range_obj, "start", None)
            range_dict["end"] = getattr(range_obj, "end", None)
            range_dict["interval"] = getattr(range_obj, "interval", None)
        return {
            "type": "range",
            "field": getattr(rp, "field", None),
            "range": range_dict,
        }
    return None


def _extract_clustering(table: Any) -> list[str] | None:
    """Extract clustering fields from a BigQuery Table."""
    if table.clustering_fields:
        return list(table.clustering_fields)
    return None


class BigQueryWarehousePlugin(CatalogClient):
    """Catalog client for BigQuery."""

    def read_catalog(self, scope: list[str], connection_config: dict[str, Any]) -> list[CatalogRelation]:
        """Read catalog metadata for the given scope.

        Scope items are dataset IDs. If an item contains a dot (e.g. 'project.dataset'),
        it is treated as project.dataset. Otherwise, connection_config['project'] is used.
        """
        # Use AnonymousCredentials when api_endpoint is set (emulator/testing)
        creds = AnonymousCredentials() if connection_config.get("api_endpoint") else get_credentials(connection_config)
        client_options = None
        if connection_config.get("api_endpoint"):
            client_options = ClientOptions(api_endpoint=connection_config["api_endpoint"])

        client = bigquery.Client(
            project=connection_config.get("project"),
            credentials=creds,
            client_options=client_options,
        )

        default_project = connection_config.get("project")
        relations: list[CatalogRelation] = []

        for scope_item in scope:
            project_id, dataset_id = _parse_scope_item(scope_item, default_project)
            dataset_ref = bigquery.DatasetReference(project_id, dataset_id)

            for table_item in client.list_tables(dataset_ref):
                table = client.get_table(table_item.reference)
                relation = self._map_table(table, project_id, dataset_id)
                relations.append(relation)

        return relations

    def _map_table(self, table: Any, project_id: str, dataset_id: str) -> CatalogRelation:
        """Map a BigQuery Table to CatalogRelation."""
        table_type = getattr(table, "table_type", "TABLE") or "TABLE"
        kind = "view" if str(table_type).upper() == "VIEW" else "table"
        namespace = CatalogNamespace(parts=[project_id, dataset_id])
        columns = [_map_schema_field(f) for f in (table.schema or [])]
        dbt_name = f"{project_id}__{dataset_id}__{table.table_id}"

        metadata: dict[str, Any] = {
            "description": table.description or None,
        }
        if table.labels:
            metadata["labels"] = dict(table.labels)

        partitioning = _extract_partitioning(table)
        if partitioning:
            metadata["partitioning"] = partitioning

        clustering = _extract_clustering(table)
        if clustering:
            metadata["clustering"] = clustering

        return CatalogRelation(
            namespace=namespace,
            name=table.table_id,
            kind=kind,
            columns=columns,
            dbt_name=dbt_name,
            metadata=metadata,
        )
