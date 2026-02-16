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
        resource = DbtResourceIR(name="my_model", meta={"owner": "bob"}, columns=[DbtColumnIR(name="id")])

        yaml_content = adapter.render_model_yaml([resource], target_version="fusion")
        data = yaml.safe_load(yaml_content)

        self.assertIn("models", data)
        model = data["models"][0]
        self.assertEqual(model["name"], "my_model")
        self.assertEqual(model["config"]["meta"], {"owner": "bob"})

    def test_render_source_yaml_project_vars(self):
        """Test that render_source_yaml supports dbt project variable pattern."""
        adapter = UnifiedDbtSchemaAdapter()
        resource = DbtResourceIR(name="my_table", columns=[DbtColumnIR(name="id")])
        db_pattern = "{{ var('databases', var('projects', {})).get('service_1', target.database) }}"

        yaml_content = adapter.render_source_yaml(
            [resource],
            target_version="dbt",
            source_name="service_1",
            database=db_pattern,
        )
        data = yaml.safe_load(yaml_content)

        self.assertEqual(data["sources"][0]["name"], "service_1")
        self.assertEqual(data["sources"][0]["database"], db_pattern)
