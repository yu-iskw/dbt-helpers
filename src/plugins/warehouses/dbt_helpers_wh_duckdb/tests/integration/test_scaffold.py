from dbt_helpers_core.orchestrator import Orchestrator
from dbt_helpers_sdk import Plan

from .base import DuckDBIntegrationTestCase


class TestDuckDBScaffold(DuckDBIntegrationTestCase):
    """Test model scaffolding with DuckDB."""

    def test_model_scaffold_integration(self):
        """Test that model scaffolding works correctly with DuckDB metadata."""
        db_path = str(self.db_path)

        # Create project config
        project_dir = self.tmp_path / "scaffold_itest"
        project_dir.mkdir()
        config_file = project_dir / "dbt_helpers.yml"
        config_file.write_text(
            f"""
warehouse:
  plugin: "duckdb"
  connection:
    db_path: "{db_path}"
target_version: "fusion"
""",
            encoding="utf-8",
        )

        orchestrator = Orchestrator(project_dir)

        # The dbt_duckdb_container should have 'users' table in 'main'
        plan = orchestrator.scaffold_models(["main"])

        assert isinstance(plan, Plan)
        assert len(plan.ops) >= 2

        # Verify SQL file content
        sql_op = next(op for op in plan.ops if str(op.path).endswith("users.sql"))
        assert "source('main', 'main__main__users')" in sql_op.content

        # Verify YAML file content
        yml_op = next(op for op in plan.ops if str(op.path).endswith("users.yml"))
        assert "models:" in yml_op.content
        assert "name: users" in yml_op.content
