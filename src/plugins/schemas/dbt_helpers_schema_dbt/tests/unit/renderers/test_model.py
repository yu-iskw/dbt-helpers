import unittest

import yaml
from dbt_helpers_schema_dbt.renderers.model import ModelRenderer

from dbt_helpers_sdk import DbtColumnIR, DbtResourceIR


class TestModelRenderer(unittest.TestCase):
    """Tests for ModelRenderer."""

    def test_render_model_yaml_fusion(self):
        renderer = ModelRenderer()
        resource = DbtResourceIR(name="my_model", meta={"owner": "bob"}, columns=[DbtColumnIR(name="id")])

        yaml_content = renderer.render_yaml([resource], target_version="fusion")
        data = yaml.safe_load(yaml_content)

        self.assertIn("models", data)
        model = data["models"][0]
        self.assertEqual(model["name"], "my_model")
        self.assertIn("config", model)
        self.assertIn("meta", model["config"])
        # Template uses context.owner (default "@"); resource.meta.owner is skipped to avoid duplicate key
        self.assertEqual(model["config"]["meta"].get("owner"), "@")

    def test_render_model_yaml_legacy(self):
        """Model YAML with legacy target still uses config block; meta from resource is included."""
        renderer = ModelRenderer()
        resource = DbtResourceIR(
            name="legacy_model",
            meta={"owner": "team"},
            tags=["staging"],
        )
        yaml_content = renderer.render_yaml([resource], target_version="legacy")
        data = yaml.safe_load(yaml_content)
        model = data["models"][0]
        self.assertEqual(model["name"], "legacy_model")
        self.assertIn("config", model)
        # Template uses context.owner (default "@"); resource.meta.owner is skipped to avoid duplicate key
        self.assertEqual(model["config"]["meta"].get("owner"), "@")

    def test_render_model_sql(self):
        """Test that render_sql generates correct SQL including source reference."""
        renderer = ModelRenderer()
        resource = DbtResourceIR(
            name="my_model",
            meta={"_extraction_metadata": {"source_name": "my_source"}},
        )
        sql_content = renderer.render_sql(resource)
        self.assertIn("with source as (", sql_content)
        self.assertIn("select * from {{ source('my_source', 'my_model') }}", sql_content)
        self.assertIn("select * from source", sql_content)

    def test_render_model_sql_default_source_name(self):
        """When _extraction_metadata is missing, source name is 'default'."""
        renderer = ModelRenderer()
        resource = DbtResourceIR(name="my_model")
        sql_content = renderer.render_sql(resource)
        self.assertIn("source('default', 'my_model')", sql_content)
