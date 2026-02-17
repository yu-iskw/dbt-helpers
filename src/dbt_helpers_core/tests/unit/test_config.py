import shutil
import tempfile
import unittest
from pathlib import Path

from dbt_helpers_core.config import ProjectConfig, WarehouseConfig, load_config


class TestConfig(unittest.TestCase):
    """Tests for the project configuration loading and models."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_load_config_defaults(self):
        config_path = self.test_dir / "dbt_helpers.yml"
        # Testing default fallback when file doesn't exist
        config = load_config(config_path)
        self.assertEqual(config.warehouse.plugin, "duckdb")
        self.assertEqual(config.target_version, "fusion")

    def test_project_config_model(self):
        config = ProjectConfig(
            warehouse=WarehouseConfig(plugin="bigquery", connection={"project": "my-project"}),
            target_version="1.11",
        )
        self.assertEqual(config.warehouse.plugin, "bigquery")
        self.assertEqual(config.target_version, "1.11")
