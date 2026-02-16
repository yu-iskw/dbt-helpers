import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dbt_helpers_core.orchestrator import Orchestrator
from dbt_helpers_sdk import CatalogNamespace, CatalogRelation, Plan


class MockWarehousePlugin:
    """Mock warehouse plugin for orchestrator tests."""

    def read_catalog(self, scope, connection_config):  # noqa: ARG002  # pylint: disable=unused-argument
        return [
            CatalogRelation(
                namespace=CatalogNamespace(parts=["raw"]),
                name="users",
                kind="table",
                columns=[],
            )
        ]


class MockSchemaPlugin:
    """Mock schema plugin for orchestrator tests."""

    def render_source_yaml(self, resources, target_version):  # noqa: ARG002  # pylint: disable=unused-argument
        return "mock yaml"

    def render_model_yaml(self, resources, target_version):  # noqa: ARG002  # pylint: disable=unused-argument
        return "mock model yaml"

    def parse_source_yaml(self, content):  # noqa: ARG002  # pylint: disable=unused-argument
        return []


class TestOrchestrator(unittest.TestCase):
    """Tests for the Orchestrator class."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_orchestrator_generate_source_plan(self):
        # Setup project dir and config
        project_dir = self.test_dir / "my_project"
        project_dir.mkdir()
        config_file = project_dir / "dbt_helpers.yml"
        config_file.write_text("warehouse:\n  plugin: mock_wh\ntarget_version: fusion")

        # Create models directory and existing source file to test UpdateYamlFile
        models_dir = project_dir / "models" / "raw"
        models_dir.mkdir(parents=True)
        existing_source = models_dir / "sources.yml"
        existing_source.write_text(
            """version: 2
sources:
  - name: raw
    tables:
      - name: users
"""
        )

        # Mock plugin discovery where it is used in orchestrator.py
        with (
            patch(
                "dbt_helpers_core.orchestrator.get_warehouse_plugins",
                return_value={"mock_wh": MockWarehousePlugin()},
            ),
            patch(
                "dbt_helpers_core.orchestrator.get_schema_plugins",
                return_value={"dbt": MockSchemaPlugin()},
            ),
        ):
            orchestrator = Orchestrator(project_dir)
            plan = orchestrator.generate_source_plan(["raw"])

            self.assertIsInstance(plan, Plan)
            self.assertEqual(len(plan.ops), 1)
            op = plan.ops[0]
            self.assertEqual(op.op_kind, "update_yaml_file")
            self.assertEqual(op.path, project_dir / "models/raw/sources.yml")
            self.assertEqual(op.patch_ops, [{"content": "mock yaml"}])

    def test_orchestrator_scaffold_models(self):
        project_dir = self.test_dir / "scaffold_project"
        project_dir.mkdir()
        config_file = project_dir / "dbt_helpers.yml"
        config_file.write_text("warehouse:\n  plugin: mock_wh\ntarget_version: fusion")

        # Mock plugins
        with (
            patch(
                "dbt_helpers_core.orchestrator.get_warehouse_plugins",
                return_value={"mock_wh": MockWarehousePlugin()},
            ),
            patch(
                "dbt_helpers_core.orchestrator.get_schema_plugins",
                return_value={"dbt": MockSchemaPlugin()},
            ),
        ):
            orchestrator = Orchestrator(project_dir)
            plan = orchestrator.scaffold_models(["raw"])

            self.assertIsInstance(plan, Plan)
            self.assertEqual(len(plan.ops), 2)  # .sql and .yml

            sql_op = next(op for op in plan.ops if str(op.path).endswith(".sql"))
            yml_op = next(op for op in plan.ops if str(op.path).endswith(".yml"))

            self.assertEqual(sql_op.op_kind, "create_file")
            self.assertIn("source('raw', 'users')", sql_op.content)
            self.assertEqual(yml_op.op_kind, "create_file")
            self.assertEqual(yml_op.content, "mock model yaml")
