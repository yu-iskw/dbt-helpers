import unittest

import yaml
from parameterized import parameterized

from dbt_helpers_schema_dbt.renderers.snapshot import SnapshotRenderer
from dbt_helpers_sdk import DbtResourceIR


class TestSnapshotRenderer(unittest.TestCase):
    """Tests for SnapshotRenderer."""

    def setUp(self):
        self.renderer = SnapshotRenderer()

    @parameterized.expand([
        ("fusion", "fusion"),
        ("legacy", "legacy"),
    ])
    def test_render_snapshot_yaml_versions(self, name, target_version):  # noqa: ARG002  # pylint: disable=unused-argument
        """Test render_yaml across different versions."""
        resource = DbtResourceIR(name="my_snapshot", description="Snapshot of orders")
        yaml_content = self.renderer.render_yaml([resource], target_version=target_version)
        data = yaml.safe_load(yaml_content)

        self.assertEqual(data.get("version"), 2)
        self.assertIn("snapshots", data)
        snapshots = data["snapshots"]
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0]["name"], "my_snapshot")
        self.assertIn("config", snapshots[0])

    @parameterized.expand([
        ("with_meta", {"_extraction_metadata": {"source_name": "my_source"}}, "source('my_source', 'my_snapshot')"),
        ("default", {}, "source('default', 'my_snapshot')"),
    ])
    def test_render_snapshot_sql_variants(self, name, meta, expected_source):  # noqa: ARG002  # pylint: disable=unused-argument
        """Test that render_sql generates correct SQL with source variants."""
        resource = DbtResourceIR(
            name="my_snapshot",
            meta=meta,
        )
        config = {
            "unique_key": "id",
            "strategy": "check",
            "check_cols": "all",
            "target_schema": "snapshots",
        }
        sql_content = self.renderer.render_sql(resource, config)

        self.assertIn("{% snapshot my_snapshot %}", sql_content)
        self.assertIn("unique_key", sql_content)
        # Handle whitespace flexibility in Jinja {{ }}
        normalized_sql = " ".join(sql_content.split())
        self.assertIn(f"{{{{ {expected_source} }}}}", normalized_sql)
        self.assertIn("{% endsnapshot %}", sql_content)
