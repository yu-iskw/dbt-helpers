import shutil
import tempfile
import unittest
from pathlib import Path

import duckdb
from dbt_helpers_wh_duckdb.plugin import DuckDBWarehousePlugin


class TestDuckDBPlugin(unittest.TestCase):
    """Tests for the DuckDBWarehousePlugin class."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_duckdb_plugin_init(self):
        plugin = DuckDBWarehousePlugin(db_path=":memory:")
        self.assertEqual(plugin.db_path, ":memory:")

    def test_duckdb_read_catalog_empty(self):
        db_path = str(self.test_dir / "test.duckdb")
        plugin = DuckDBWarehousePlugin(db_path=db_path)

        # Create empty database
        conn = duckdb.connect(db_path)
        conn.execute("CREATE SCHEMA raw")
        conn.close()

        relations = plugin.read_catalog(["raw"], connection_config={})
        self.assertEqual(len(relations), 0)
