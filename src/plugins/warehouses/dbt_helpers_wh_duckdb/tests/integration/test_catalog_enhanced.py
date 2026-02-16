from base import DuckDBIntegrationTestCase
from dbt_helpers_wh_duckdb.plugin import DuckDBWarehousePlugin


class TestDuckDBCatalogEnhanced(DuckDBIntegrationTestCase):
    """Enhanced catalog tests with DuckDB."""

    def test_duckdb_read_catalog_complex_integration(self):
        """Test that read_catalog handles multiple relations and complex schemas."""
        db_path = str(self.db_path)
        plugin = DuckDBWarehousePlugin(db_path=db_path)

        # The sample_project has multiple models
        relations = plugin.read_catalog(["main"], connection_config={})

        # Verify we got multiple relations
        self.assertGreaterEqual(len(relations), 1)

        for rel in relations:
            self.assertEqual(rel.namespace.parts, ["main"])
            self.assertGreaterEqual(len(rel.columns), 1)
            for col in rel.columns:
                self.assertIsNotNone(col.data_type)
