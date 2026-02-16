from dbt_helpers_wh_duckdb.plugin import DuckDBWarehousePlugin


def test_duckdb_read_catalog_complex_integration(dbt_duckdb_container):
    db_path = str(dbt_duckdb_container)
    plugin = DuckDBWarehousePlugin(db_path=db_path)

    # The sample_project has multiple models
    relations = plugin.read_catalog(["main"], connection_config={})

    # Verify we got multiple relations (users and potentially others if added to sample_project)
    assert len(relations) >= 1

    for rel in relations:
        assert rel.namespace.parts == ["main"]
        assert len(rel.columns) >= 1
        for col in rel.columns:
            assert col.data_type is not None
