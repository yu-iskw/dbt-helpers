"""Integration tests for BigQuery plugin against the emulator."""

from dbt_helpers_wh_bigquery.plugin import BigQueryWarehousePlugin


def test_read_catalog_with_emulator(bigquery_emulator):
    """Plugin reads catalog from emulator after seeding a table."""
    config = bigquery_emulator
    project = config["project"]
    api_endpoint = config["api_endpoint"]

    # Run plugin
    connection_config = {
        "project": project,
        "api_endpoint": api_endpoint,
    }
    plugin = BigQueryWarehousePlugin()
    relations = plugin.read_catalog(["dataset1"], connection_config)

    assert len(relations) >= 1
    # Check for the all_types table created by dbt
    table_rels = [r for r in relations if r.name == "all_types"]
    assert len(table_rels) == 1
    rel = table_rels[0]
    assert rel.namespace.parts == [project, "dataset1"]
    assert rel.kind == "table"
    assert len(rel.columns) >= 2
    col_names = [c.name for c in rel.columns]
    assert "i" in col_names
    assert "s" in col_names
