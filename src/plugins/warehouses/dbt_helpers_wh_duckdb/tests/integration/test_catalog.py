import pytest

from dbt_helpers_wh_duckdb.plugin import DuckDBWarehousePlugin

from .base import DuckDBIntegrationTestCase


@pytest.mark.parametrize("scenario_name", ["sample_project"], indirect=True)
class TestDuckDBCatalog(DuckDBIntegrationTestCase):
    """Test catalog reading with DuckDB."""

    def test_duckdb_read_catalog_integration(self):
        """Test that read_catalog correctly extracts metadata from a real DuckDB."""
        db_path = str(self.db_path)
        plugin = DuckDBWarehousePlugin(db_path=db_path)

        # dbt default schema for DuckDB is 'main'
        relations = plugin.read_catalog(["main"], connection_config={})

        assert len(relations) >= 1

        users_rel = next((r for r in relations if r.name == "users"), None)
        assert users_rel is not None
        assert users_rel.namespace.parts == ["main"]

        col_names = [c.name for c in users_rel.columns]
        assert "id" in col_names
        assert "name" in col_names
