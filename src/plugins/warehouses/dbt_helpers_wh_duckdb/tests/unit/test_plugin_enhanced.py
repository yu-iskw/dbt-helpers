import shutil
import tempfile
import unittest
from pathlib import Path

import duckdb
from dbt_helpers_wh_duckdb.plugin import DuckDBWarehousePlugin


class TestDuckDBPluginEnhanced(unittest.TestCase):
    """Enhanced tests for the DuckDBWarehousePlugin class covering multiple relations."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_duckdb_read_catalog_bulk(self):
        db_path = str(self.test_dir / "test.duckdb")
        conn = duckdb.connect(db_path)

        # Create test data
        conn.execute("CREATE SCHEMA raw")
        conn.execute("CREATE TABLE raw.users (id INTEGER, name VARCHAR)")
        conn.execute("CREATE TABLE raw.orders (id INTEGER, user_id INTEGER, amount DOUBLE)")
        conn.execute(
            """
            CREATE VIEW raw.user_summary AS
            SELECT name, count(*)
            FROM raw.users
            JOIN raw.orders ON users.id = orders.user_id
            GROUP BY 1
            """
        )
        conn.close()

        plugin = DuckDBWarehousePlugin(db_path=db_path)
        relations = plugin.read_catalog(["raw"], connection_config={})

        self.assertEqual(len(relations), 3)

        users = next(r for r in relations if r.name == "users")
        self.assertEqual(users.kind, "table")
        self.assertEqual(len(users.columns), 2)
        self.assertEqual(users.columns[0].name, "id")
        self.assertEqual(users.columns[1].name, "name")

        orders = next(r for r in relations if r.name == "orders")
        self.assertEqual(orders.kind, "table")
        self.assertEqual(len(orders.columns), 3)

        summary = next(r for r in relations if r.name == "user_summary")
        self.assertEqual(summary.kind, "view")
        self.assertEqual(len(summary.columns), 2)

    def test_duckdb_read_catalog_empty_schema(self):
        db_path = str(self.test_dir / "empty.duckdb")
        conn = duckdb.connect(db_path)
        conn.execute("CREATE SCHEMA empty")
        conn.close()

        plugin = DuckDBWarehousePlugin(db_path=db_path)
        relations = plugin.read_catalog(["empty"], connection_config={})
        self.assertEqual(len(relations), 0)

    def test_duckdb_read_catalog_missing_schema(self):
        db_path = str(self.test_dir / "missing.duckdb")
        plugin = DuckDBWarehousePlugin(db_path=db_path)
        relations = plugin.read_catalog(["non_existent"], connection_config={})
        self.assertEqual(len(relations), 0)
