import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dbt_helpers_core.orchestrator import Orchestrator
from dbt_helpers_sdk import CatalogNamespace, CatalogRelation, CreateFile, Plan


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


class MockSchemaPlugin:  # pylint: disable=unused-argument
    """Mock schema plugin for orchestrator tests."""

    def render_source_yaml(
        self, resources, target_version, source_name="raw", database=None, context=None  # noqa: ARG002
    ):
        self.last_source_name = source_name
        self.last_database = database
        return "mock yaml"

    def render_model_yaml(self, resources, target_version, database=None, context=None):  # noqa: ARG002
        return "mock model yaml"

    def render_model_sql(self, resource, database=None, context=None):  # noqa: ARG002
        source_name = resource.meta.get("_extraction_metadata", {}).get("source_name", "raw")
        return f"select * from {{{{ source('{source_name}', '{resource.name}') }}}}"  # nosec B608

    def render_model_doc(self, resource, context=None):  # noqa: ARG002
        return "mock model doc"

    def parse_source_yaml(self, content):  # noqa: ARG002
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

    def test_orchestrator_generate_source_plan_env_vars(self):
        """Test that generate_source_plan passes correct env var patterns."""
        project_dir = self.test_dir / "env_var_project"
        project_dir.mkdir()
        (project_dir / "dbt_helpers.yml").write_text("warehouse:\n  plugin: mock_wh\ntarget_version: dbt")

        mock_wh = MockWarehousePlugin()
        mock_schema = MockSchemaPlugin()

        with (
            patch("dbt_helpers_core.orchestrator.get_warehouse_plugins", return_value={"mock_wh": mock_wh}),
            patch("dbt_helpers_core.orchestrator.get_schema_plugins", return_value={"dbt": mock_schema}),
        ):
            orchestrator = Orchestrator(project_dir)
            orchestrator.generate_source_plan(["raw"])

            # Verify that mock_schema received the correct parameters
            self.assertEqual(mock_schema.last_source_name, "raw")
            expected_db_pattern = "{{ var('databases', var('projects', {})).get('raw', target.database) }}"
            self.assertEqual(mock_schema.last_database, expected_db_pattern)

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
            self.assertEqual(len(plan.ops), 3)  # .sql, .yml, and .md doc

            sql_op = next(op for op in plan.ops if str(op.path).endswith(".sql"))
            yml_op = next(op for op in plan.ops if str(op.path).endswith(".yml"))

            self.assertEqual(sql_op.op_kind, "create_file")
            self.assertIn("source('raw', 'users')", sql_op.content)
            self.assertEqual(yml_op.op_kind, "create_file")
            self.assertEqual(yml_op.content, "mock model yaml")

    def test_orchestrator_apply_plan(self):
        project_dir = self.test_dir / "apply_project"
        project_dir.mkdir()

        plan = Plan()
        file_path = Path("new_file.txt")
        plan.add_op(CreateFile(path=file_path, content="hello"))

        orchestrator = Orchestrator(project_dir)
        orchestrator.apply_plan(plan)

        full_path = project_dir / file_path
        self.assertTrue(full_path.exists())
        self.assertEqual(full_path.read_text(), "hello")

        # Check audit log
        audit_log = project_dir / ".dbt_helpers" / "audit.jsonl"
        self.assertTrue(audit_log.exists())
