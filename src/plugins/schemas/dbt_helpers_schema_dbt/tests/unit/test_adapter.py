import unittest

import yaml
from dbt_helpers_schema_dbt.adapter import UnifiedDbtSchemaAdapter

from dbt_helpers_sdk import DbtColumnIR, DbtResourceIR


class TestDbtSchemaAdapter(unittest.TestCase):
    """Tests for UnifiedDbtSchemaAdapter."""

    def test_render_source_yaml_fusion(self):
        adapter = UnifiedDbtSchemaAdapter()
        resource = DbtResourceIR(
            name="my_table",
            meta={"owner": "alice"},
            tags=["pii"],
            columns=[DbtColumnIR(name="id")],
        )

        yaml_content = adapter.render_source_yaml([resource], target_version="fusion")
        data = yaml.safe_load(yaml_content)

        table = data["sources"][0]["tables"][0]
        self.assertIn("config", table)
        self.assertEqual(table["config"]["meta"], {"owner": "alice"})
        self.assertEqual(table["config"]["tags"], ["pii"])
        self.assertNotIn("meta", table)  # Should be under config

    def test_render_source_yaml_legacy(self):
        adapter = UnifiedDbtSchemaAdapter()
        resource = DbtResourceIR(
            name="my_table",
            meta={"owner": "alice"},
            tags=["pii"],
            columns=[DbtColumnIR(name="id")],
        )

        yaml_content = adapter.render_source_yaml([resource], target_version="legacy")
        data = yaml.safe_load(yaml_content)

        table = data["sources"][0]["tables"][0]
        self.assertEqual(table["meta"], {"owner": "alice"})
        self.assertEqual(table["tags"], ["pii"])
        self.assertNotIn("config", table)

    def test_render_model_yaml_fusion(self):
        adapter = UnifiedDbtSchemaAdapter()
        resource = DbtResourceIR(
            name="my_model", meta={"owner": "bob"}, columns=[DbtColumnIR(name="id")]
        )

        yaml_content = adapter.render_model_yaml([resource], target_version="fusion")
        data = yaml.safe_load(yaml_content)

        self.assertIn("models", data)
        model = data["models"][0]
        self.assertEqual(model["name"], "my_model")
        self.assertEqual(model["config"]["meta"], {"owner": "bob"})
