from typing import Any

import duckdb

from dbt_helpers_sdk import (
    CatalogClient,
    CatalogColumn,
    CatalogNamespace,
    CatalogRelation,
)


class DuckDBWarehousePlugin(CatalogClient):
    """Catalog client for DuckDB databases."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path

    def read_catalog(
        self, scope: list[str], connection_config: dict[str, Any]
    ) -> list[CatalogRelation]:
        db_path = connection_config.get("db_path", self.db_path)
        # Connect to the database
        conn = duckdb.connect(db_path)
        relations = []

        try:
            for schema in scope:
                # Query all columns in the schema in one go
                # This avoids N+1 queries
                cols_data = conn.execute(
                    """
                    SELECT table_name, column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = ?
                    ORDER BY table_name, ordinal_position
                """,
                    [schema],
                ).fetchall()

                # Group columns by table
                table_to_cols: dict[str, list[CatalogColumn]] = {}
                for table_name, col_name, data_type, is_nullable in cols_data:
                    if table_name not in table_to_cols:
                        table_to_cols[table_name] = []
                    table_to_cols[table_name].append(
                        CatalogColumn(
                            name=col_name,
                            data_type=data_type,
                            nullable=(is_nullable == "YES"),
                        )
                    )

                # Also fetch tables (including views) to ensure we have all relations
                tables = conn.execute(
                    """
                    SELECT table_name, table_type
                    FROM information_schema.tables
                    WHERE table_schema = ?
                """,
                    [schema],
                ).fetchall()

                for table_name, table_type in tables:
                    kind = "table" if table_type == "BASE TABLE" else "view"
                    columns = table_to_cols.get(table_name, [])

                    relations.append(
                        CatalogRelation(
                            namespace=CatalogNamespace(parts=[schema]),
                            name=table_name,
                            kind=kind,
                            columns=columns,
                            metadata={
                                "meta": {"owner": "test_team"},  # Default for MVP
                                "tags": ["raw_data"],
                                "description": f"Raw {kind} {table_name}",
                            },
                        )
                    )
        finally:
            conn.close()

        return relations
