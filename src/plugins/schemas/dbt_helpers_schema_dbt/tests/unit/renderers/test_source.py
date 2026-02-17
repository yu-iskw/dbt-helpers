import unittest

import yaml
from dbt_helpers_schema_dbt.renderers.source import SourceRenderer
from parameterized import parameterized

from dbt_helpers_sdk import DbtColumnIR, DbtResourceIR


class TestSourceRenderer(unittest.TestCase):
    """Tests for SourceRenderer."""

    def setUp(self):
        self.renderer = SourceRenderer()

    @parameterized.expand([
        ("fusion", "fusion", "alice"),
        ("legacy", "legacy", "alice"),
        ("dbt", "dbt", None),
    ])
    def test_render_source_yaml_versions(self, name, target_version, owner):  # noqa: ARG002  # pylint: disable=unused-argument
        """Test render_yaml with different dbt versions and configurations."""
        resource = DbtResourceIR(
            name="my_table",
            meta={"owner": owner} if owner else {},
            tags=["pii"],
            columns=[DbtColumnIR(name="id")],
        )

        yaml_content = self.renderer.render_yaml([resource], target_version=target_version)
        data = yaml.safe_load(yaml_content)

        table = data["sources"][0]["tables"][0]
        self.assertIn("config", table)

        if owner:
            # Source template puts meta under labels
            self.assertEqual(table["config"]["meta"]["labels"].get("owner"), owner)

        if target_version != "dbt":
            self.assertIn("pii", table["config"]["tags"])

    def test_render_source_yaml_project_vars(self):
        """Test that render_yaml supports dbt project variable pattern."""
        resource = DbtResourceIR(name="my_table", columns=[DbtColumnIR(name="id")])
        db_pattern = "{{ var('databases', var('projects', {})).get('service_1', target.database) }}"

        yaml_content = self.renderer.render_yaml(
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
        resources = [
            DbtResourceIR(name="table_one", columns=[DbtColumnIR(name="id")]),
            DbtResourceIR(name="table_two", columns=[DbtColumnIR(name="id")]),
        ]
        yaml_content = self.renderer.render_yaml(
            resources, target_version="fusion", source_name="raw"
        )
        data = yaml.safe_load(yaml_content)
        tables = data["sources"][0]["tables"]
        self.assertEqual(len(tables), 2)
        # Source template uses table name directly as dbt source name
        self.assertEqual(tables[0]["name"], "table_one")
        self.assertEqual(tables[1]["name"], "table_two")

    def test_parse_source_yaml(self):
        """Test parsing dbt source YAML back into IR."""
        yaml_content = """
version: 2
sources:
  - name: my_source
    database: my_db
    tables:
      - name: my_table
        identifier: real_table
        description: "A description"
        config:
          meta:
            labels:
              owner: "alice"
          tags: ["pii"]
        columns:
          - name: col1
            description: "Col description"
            data_tests:
              - unique
"""
        resources = self.renderer.parse_yaml(yaml_content)
        self.assertEqual(len(resources), 1)
        res = resources[0]
        self.assertEqual(res.name, "my_table")
        self.assertEqual(res.description, "A description")
        # Parser currently doesn't flatten labels, so it will be in the meta dict
        self.assertEqual(res.meta.get("labels", {}).get("owner"), "alice")
        self.assertIn("pii", res.tags)
        self.assertEqual(len(res.columns), 1)
        self.assertEqual(res.columns[0].name, "col1")
        self.assertEqual(res.columns[0].tests[0], {"unique": {}})
