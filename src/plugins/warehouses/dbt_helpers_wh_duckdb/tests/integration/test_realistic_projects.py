import pytest

from dbt_helpers_core.orchestrator import Orchestrator
from dbt_helpers_sdk import CreateFile

from .base import DuckDBIntegrationTestCase


@pytest.mark.parametrize("scenario_name", ["jaffle_shop"], indirect=True)
class TestRealisticProjects(DuckDBIntegrationTestCase):
    """Integration tests using realistic dbt projects."""

    def test_jaffle_shop_source_import(self):
        """Test that we can import sources from the jaffle_shop project."""
        db_path = str(self.db_path)

        # Setup dbt-helpers project
        project_dir = self.tmp_path / "helpers_project"
        project_dir.mkdir()

        config_file = project_dir / "dbt_helpers.yml"
        config_file.write_text(
            f"""
warehouse:
  plugin: "duckdb"
  connection:
    db_path: "{db_path}"
target_version: "dbt"
paths:
  source: "models/staging/{{{{ table }}}}.yml"
""",
            encoding="utf-8",
        )

        orchestrator = Orchestrator(project_dir)

        # jaffle_shop build should have created tables in 'main' schema
        # tables: customers, orders, stg_customers, stg_orders, raw_customers, raw_orders, raw_payments
        plan = orchestrator.generate_source_plan(["main"])

        # Verify that we see some of the expected tables
        # DuckDB plugin uses dbt_name schema__table for path if not using {table} in template
        # Wait, if template is "models/staging/{{ table }}.yml", then {table} is used.
        # In PathPolicy, variables["table"] is relation.name.

        create_ops = [op for op in plan.ops if isinstance(op, CreateFile)]
        table_names = [op.path.stem for op in create_ops]

        # DuckDB plugin prefixes with schema name (main__)
        assert "main__customers" in table_names
        assert "main__orders" in table_names
        assert "main__stg_customers" in table_names
        assert "main__raw_customers" in table_names
        assert "main__raw_orders" in table_names
        assert "main__raw_payments" in table_names

    def test_jaffle_shop_catalog_content(self):
        """Verify that imported source YAMLs have correct metadata for jaffle_shop."""
        db_path = str(self.db_path)

        project_dir = self.tmp_path / "catalog_project"
        project_dir.mkdir()

        (project_dir / "dbt_helpers.yml").write_text(
            f"""
warehouse:
  plugin: "duckdb"
  connection:
    db_path: "{db_path}"
target_version: "dbt"
paths:
  source: "models/staging/{{{{ table }}}}.yml"
""",
            encoding="utf-8",
        )

        orchestrator = Orchestrator(project_dir)
        plan = orchestrator.generate_source_plan(["main"])

        # Find raw_customers (prefixed with main__)
        customers_op = next(op for op in plan.ops if "main__raw_customers" in str(op.path))
        content = customers_op.content

        assert "name: main__raw_customers" in content
        assert "columns:" in content
        # raw_customers has id, first_name, last_name
        assert "name: id" in content
        assert "name: first_name" in content
        assert "name: last_name" in content
