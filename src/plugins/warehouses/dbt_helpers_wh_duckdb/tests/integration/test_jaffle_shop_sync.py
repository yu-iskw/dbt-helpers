import pytest

from dbt_helpers_core.orchestrator import Orchestrator

from .base import DuckDBIntegrationTestCase


@pytest.mark.parametrize("scenario_name", ["jaffle_shop"], indirect=True)
class TestJaffleShopSync(DuckDBIntegrationTestCase):
    """Integration tests using the jaffle_shop directory scenario."""

    def test_jaffle_shop_source_import(self):
        """Test importing sources from the jaffle_shop database."""
        project_dir = self.tmp_path / "project"
        project_dir.mkdir()

        # Create dbt_helpers.yml
        (project_dir / "dbt_helpers.yml").write_text(
            f"""
warehouse:
  plugin: "duckdb"
  connection:
    db_path: "{self.db_path}"
target_version: "dbt"
paths:
  source: "models/staging/{{{{ table }}}}.yml"
""",
            encoding="utf-8",
        )

        orchestrator = Orchestrator(project_dir)

        # jaffle_shop tables are in 'main' schema in DuckDB
        plan = orchestrator.generate_source_plan(["main"])

        # Should discover multiple tables
        assert len(plan.ops) > 0
        orchestrator.apply_plan(plan)

        # Verify some generated files
        # Table names in DuckDB will be 'raw_customers', 'raw_orders', etc.
        # But DuckDB plugin prefixes them with the schema name 'main__' as per ADR 0030
        assert (project_dir / "models/staging/main__raw_customers.yml").exists()
        assert (project_dir / "models/staging/main__raw_orders.yml").exists()

        content = (project_dir / "models/staging/main__raw_customers.yml").read_text()
        assert "name: main__raw_customers" in content
        assert "columns:" in content
