import unittest

import yaml
from dbt_helpers_schema_dbt.renderers.source import SourceRenderer

from dbt_helpers_sdk import DbtColumnIR, DbtResourceIR


class TestSourceRenderer(unittest.TestCase):
    """Tests for SourceRenderer."""

    def test_render_source_yaml_fusion(self):
        renderer = SourceRenderer()
        resource = DbtResourceIR(
            name="my_table",
            meta={"owner": "alice"},
            tags=["pii"],
            columns=[DbtColumnIR(name="id")],
        )

        yaml_content = renderer.render_yaml([resource], target_version="fusion")
        data = yaml.safe_load(yaml_content)

        table = data["sources"][0]["tables"][0]
        self.assertIn("config", table)
        self.assertIn("meta", table["config"])
        self.assertIn("labels", table["config"]["meta"])
        self.assertEqual(table["config"]["meta"]["labels"].get("owner"), "alice")
        self.assertIn("tags", table["config"])

    def test_render_source_yaml_legacy(self):
        renderer = SourceRenderer()
        resource = DbtResourceIR(
            name="my_table",
            meta={"owner": "alice"},
            tags=["pii"],
            columns=[DbtColumnIR(name="id")],
        )

        yaml_content = renderer.render_yaml([resource], target_version="legacy")
        data = yaml.safe_load(yaml_content)

        table = data["sources"][0]["tables"][0]
        self.assertEqual(table["identifier"], "my_table")
        self.assertIn("config", table)
        self.assertEqual(table["config"]["meta"]["labels"].get("owner"), "alice")
        self.assertIn("pii", table["config"]["tags"])

    def test_render_source_yaml_project_vars(self):
        """Test that render_yaml supports dbt project variable pattern."""
        renderer = SourceRenderer()
        resource = DbtResourceIR(name="my_table", columns=[DbtColumnIR(name="id")])
        db_pattern = "{{ var('databases', var('projects', {})).get('service_1', target.database) }}"

        yaml_content = renderer.render_yaml(
            [resource],
            target_version="dbt",
            source_name="service_1",
            database=db_pattern,
        )
        data = yaml.safe_load(yaml_content)

        self.assertIn("sources", data)
        self.assertEqual(len(data["sources"]), 1)
        self.assertIn("database", data["sources"][0])
        self.assertIn("var(", data["sources"][0]["database"])

    def test_render_source_yaml_multiple_tables(self):
        """Multiple resources produce multiple table entries under one source."""
        renderer = SourceRenderer()
        resources = [
            DbtResourceIR(name="table_one", columns=[DbtColumnIR(name="id")]),
            DbtResourceIR(name="table_two", columns=[DbtColumnIR(name="id")]),
        ]
        yaml_content = renderer.render_yaml(
            resources, target_version="fusion", source_name="raw"
        )
        data = yaml.safe_load(yaml_content)
        tables = data["sources"][0]["tables"]
        self.assertEqual(len(tables), 2)
        self.assertEqual(tables[0]["identifier"], "table_one")
        self.assertEqual(tables[1]["identifier"], "table_two")

    def test_render_source_yaml_without_database(self):
        """When database is not passed, source has no database key."""
        renderer = SourceRenderer()
        resource = DbtResourceIR(name="t", columns=[DbtColumnIR(name="id")])
        yaml_content = renderer.render_yaml(
            [resource], target_version="fusion", source_name="raw"
        )
        data = yaml.safe_load(yaml_content)
        source = data["sources"][0]
        self.assertIn("tables", source)
        self.assertEqual(len(source["tables"]), 1)
        self.assertEqual(source["tables"][0]["identifier"], "t")
