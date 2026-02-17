import re
import shutil
import tempfile
import unittest
from pathlib import Path

import duckdb

from dbt_helpers_core.orchestrator import Orchestrator


class TestDuckDBSyncScenarios(unittest.TestCase):
    """Scenario-driven integration tests for DuckDB source sync."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_path = Path(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_sync_description_scenario(self):
        """Verify that table-level description is synced from warehouse."""
        db_path = self.tmp_path / "desc_test.duckdb"
        conn = duckdb.connect(str(db_path))
        conn.execute("CREATE TABLE main.users (id INTEGER, name VARCHAR)")
        conn.close()

        project_dir = self.tmp_path / "project"
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

        # 1. Initial import
        plan1 = orchestrator.generate_source_plan(["main"])
        orchestrator.apply_plan(plan1)

        yml_path = project_dir / "models/staging/main__users.yml"
        content = yml_path.read_text()
        assert "description: |" in content
        assert "Raw table users" in content

        # 2. Remove description manually from YAML
        new_content = re.sub(r"description: \|.*Raw table users", "description: ''", content, flags=re.DOTALL)
        yml_path.write_text(new_content)

        # 3. Sync
        plan2 = orchestrator.sync_sources(["main"])
        assert len(plan2.ops) == 1
        orchestrator.apply_plan(plan2)

        final_content = yml_path.read_text()
        # It might be rendered as 'description: Raw table users' or 'description: |- \n Raw table users'
        assert "Raw table users" in final_content

    def test_idempotency_scenario(self):
        """Verify that a second sync run produces no changes."""
        db_path = self.tmp_path / "idempotency_test.duckdb"
        conn = duckdb.connect(str(db_path))
        conn.execute("CREATE TABLE main.users (id INTEGER, name VARCHAR)")
        conn.close()

        project_dir = self.tmp_path / "project"
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
        orchestrator.apply_plan(orchestrator.generate_source_plan(["main"]))

        # Second run
        plan2 = orchestrator.sync_sources(["main"])
        assert len(plan2.ops) == 0

    def test_add_column_scenario(self):
        """Verify that new warehouse columns are added to dbt source."""
        db_path = self.tmp_path / "add_col.duckdb"
        conn = duckdb.connect(str(db_path))
        conn.execute("CREATE TABLE main.users (id INTEGER, name VARCHAR)")
        conn.close()

        project_dir = self.tmp_path / "project"
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
        orchestrator.apply_plan(orchestrator.generate_source_plan(["main"]))

        # Add column in warehouse
        conn = duckdb.connect(str(db_path))
        conn.execute("ALTER TABLE main.users ADD COLUMN email VARCHAR")
        conn.close()

        # Sync
        plan = orchestrator.sync_sources(["main"])
        assert len(plan.ops) == 1
        orchestrator.apply_plan(plan)

        yml_path = project_dir / "models/staging/main__users.yml"
        final_content = yml_path.read_text()
        assert "name: email" in final_content

if __name__ == "__main__":
    unittest.main()
