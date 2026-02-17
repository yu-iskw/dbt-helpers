"""Integration tests for BigQuery data type mapping via the emulator."""

from dbt_helpers_wh_bigquery.plugin import BigQueryWarehousePlugin


def test_all_data_types(bigquery_emulator):
    """Plugin correctly maps all BigQuery data types from catalog."""
    config = bigquery_emulator
    project = config["project"]
    api_endpoint = config["api_endpoint"]

    connection_config = {
        "project": project,
        "api_endpoint": api_endpoint,
    }
    plugin = BigQueryWarehousePlugin()
    relations = plugin.read_catalog(["dataset1"], connection_config)

    # Table name is 'all_types' (from all_types.sql)
    table_rels = [r for r in relations if r.name == "all_types"]
    assert len(table_rels) == 1, f"Expected all_types, got {[r.name for r in relations]}"
    rel = table_rels[0]

    expected_types = {
        "s": "STRING",
        "b": "BYTES",
        "i": "INT64",
        "f": "FLOAT64",
        "bool_col": "BOOL",
        "ts": "TIMESTAMP",
        "d": "DATE",
        "t": "TIME",
        "dt": "DATETIME",
        "geo": "GEOGRAPHY",
        "json_col": "JSON",
        "interval_col": "INTERVAL",
        "s10": "STRING(10)",
        "b10": "BYTES(10)",
        "num": "NUMERIC(10, 2)",
        "bignum": "BIGNUMERIC(20, 5)",
        "arr_str": "ARRAY<STRING>",
        "rec": "STRUCT<sub_int INT64, sub_str STRING>",
        "coords": "ARRAY<STRUCT<x FLOAT64, y FLOAT64>>",
        "r_date": "RANGE<DATE>",
        "r_datetime": "RANGE<DATETIME>",
        "r_timestamp": "RANGE<TIMESTAMP>",
    }

    col_map = {c.name: c.data_type for c in rel.columns}
    for col_name, expected_type in expected_types.items():
        assert col_name in col_map, f"Column {col_name} not found in {list(col_map.keys())}"
        assert col_map[col_name] == expected_type, (
            f"Column {col_name}: expected {expected_type}, got {col_map[col_name]}"
        )
