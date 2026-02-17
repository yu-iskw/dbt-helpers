import unittest

import yaml
from parameterized import parameterized

from dbt_helpers_schema_dbt.renderers.model import ModelRenderer
from dbt_helpers_sdk import DbtColumnIR, DbtResourceIR


class TestModelRenderer(unittest.TestCase):
    """Tests for ModelRenderer."""

    def setUp(self):
        self.renderer = ModelRenderer()

    @parameterized.expand([
        ("fusion", "fusion"),
        ("legacy", "legacy"),
        ("dbt", "dbt"),
    ])
    def test_render_model_yaml_versions(self, name, target_version):  # noqa: ARG002  # pylint: disable=unused-argument
        """Test render_yaml with different dbt versions."""
        resource = DbtResourceIR(
            name="my_model",
            meta={"owner": "bob", "other": "value"},
            columns=[DbtColumnIR(name="id")]
        )

        yaml_content = self.renderer.render_yaml([resource], target_version=target_version)
        data = yaml.safe_load(yaml_content)

        self.assertIn("models", data)
        model = data["models"][0]
        self.assertEqual(model["name"], "my_model")
        self.assertIn("config", model)
        self.assertIn("meta", model["config"])
        # Template uses context.owner (default "@"); resource.meta.owner is skipped to avoid duplicate key
        self.assertEqual(model["config"]["meta"].get("owner"), "@")
        self.assertEqual(model["config"]["meta"].get("other"), "value")

    @parameterized.expand([
        ("with_meta", {"_extraction_metadata": {"source_name": "my_source"}}, "source('my_source', 'my_model')"),
        ("default", {}, "source('default', 'my_model')"),
    ])
    def test_render_model_sql_variants(self, name, meta, expected_source):  # noqa: ARG002  # pylint: disable=unused-argument
        """Test that render_sql generates correct SQL including source reference variants."""
        resource = DbtResourceIR(
            name="my_model",
            meta=meta,
        )
        sql_content = self.renderer.render_sql(resource)
        self.assertIn("with source as (", sql_content)
        # Handle whitespace flexibility in Jinja {{ }}
        normalized_sql = " ".join(sql_content.split())
        self.assertIn(f"{{{{ {expected_source} }}}}", normalized_sql)
        self.assertIn("select * from source", sql_content)

    def test_render_model_doc(self):
        """Test render_doc generates correct Markdown documentation."""
        resource = DbtResourceIR(name="my_model")
        # Template uses context which might have dbt_helper_version
        doc_content = self.renderer.render_doc(resource)

        self.assertIn("{% docs my_model %}", doc_content)
        self.assertIn("## Overview", doc_content)
        self.assertIn("{%- enddocs %}", doc_content)

    def test_parse_model_yaml(self):
        """Test parsing dbt model YAML back into IR."""
        yaml_content = """
version: 2
models:
  - name: parsed_model
    description: "A description"
    config:
      meta:
        owner: "@someone"
        contains_pii: "true"
      tags: ["tag1"]
    columns:
      - name: col1
        description: "Col description"
        data_tests:
          - unique
"""
        resources = self.renderer.parse_yaml(yaml_content)
        self.assertEqual(len(resources), 1)
        res = resources[0]
        self.assertEqual(res.name, "parsed_model")
        self.assertEqual(res.description, "A description")
        self.assertEqual(res.meta.get("owner"), "@someone")
        self.assertEqual(res.meta.get("contains_pii"), "true")
        self.assertIn("tag1", res.tags)
        self.assertEqual(len(res.columns), 1)
        self.assertEqual(res.columns[0].name, "col1")
        self.assertEqual(res.columns[0].tests[0], {"unique": {}})
