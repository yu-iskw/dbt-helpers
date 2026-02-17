import unittest

import yaml
from dbt_helpers_schema_dbt.renderers.snapshot import SnapshotRenderer

from dbt_helpers_sdk import DbtResourceIR


class TestSnapshotRenderer(unittest.TestCase):
    """Tests for SnapshotRenderer."""

    def test_render_snapshot_yaml_minimal(self):
        """Single snapshot with only name/description produces valid YAML and config block."""
        renderer = SnapshotRenderer()
        resource = DbtResourceIR(name="my_snapshot", description="Snapshot of orders")
        yaml_content = renderer.render_yaml([resource], target_version="fusion")
        data = yaml.safe_load(yaml_content)
        self.assertEqual(data.get("version"), 2)
        self.assertIn("snapshots", data)
        snapshots = data["snapshots"]
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0]["name"], "my_snapshot")
        self.assertEqual(snapshots[0]["description"], "Snapshot of orders")
        self.assertIn("config", snapshots[0])
        self.assertIs(snapshots[0]["config"]["enabled"], True)
        # full_refresh may be rendered as 'none' (string) or null in YAML
        self.assertIn("full_refresh", snapshots[0]["config"])

    def test_render_snapshot_sql(self):
        """Test that render_sql generates correct SQL."""
        renderer = SnapshotRenderer()
        resource = DbtResourceIR(
            name="my_snapshot",
            meta={"_extraction_metadata": {"source_name": "my_source"}},
        )
        config = {
            "unique_key": "id",
            "strategy": "check",
            "check_cols": "all",
            "target_schema": "snapshots",
        }
        sql_content = renderer.render_sql(resource, config)

        self.assertIn("{% snapshot my_snapshot %}", sql_content)
        self.assertIn("unique_key", sql_content)
        self.assertIn("id", sql_content)
        self.assertIn("target_schema", sql_content)
        self.assertIn("snapshots", sql_content)
        self.assertIn("select * from {{ source('my_source', 'my_snapshot') }}", sql_content)
        self.assertIn("{% endsnapshot %}", sql_content)

    def test_render_snapshot_sql_default_source_name(self):
        """When _extraction_metadata is missing, source name is 'default'."""
        renderer = SnapshotRenderer()
        resource = DbtResourceIR(name="my_snap")
        config = {"unique_key": "id", "target_schema": "snapshots"}
        sql_content = renderer.render_sql(resource, config)
        self.assertIn("source('default', 'my_snap')", sql_content)
