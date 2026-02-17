import shutil
import tempfile
import unittest
from pathlib import Path

import duckdb

from dbt_helpers_core.orchestrator import Orchestrator
from dbt_helpers_sdk import UpdateYamlFile


class TestDuckDBSourceSync(unittest.TestCase):
    """Test that source synchronization correctly patches existing YAML files."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_path = Path(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_source_sync_full_scenario(self):
        """Scenario for source synchronization."""
        db_path = self.tmp_path / "sync_test.duckdb"
        conn = duckdb.connect(str(db_path))
        conn.execute("CREATE TABLE main.my_table (id INTEGER, name VARCHAR, age INTEGER)")
        conn.close()

        project_dir = self.tmp_path / "sync_project"
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

        yml_path = project_dir / "models/staging/main__my_table.yml"
        assert yml_path.exists()

        # 2. Manually edit YAML to add a description
        content = yml_path.read_text(encoding="utf-8")
        # Find 'name: id' and add description below it
        lines = content.splitlines()

        filtered_lines = []
        skip = False
        for line in lines:
            if skip:
                skip = False
                continue
            if "name: id" in line:
                filtered_lines.append(line)
                filtered_lines.append("            description: 'The unique ID'")
                skip = True # Skip the existing description line
            else:
                filtered_lines.append(line)

        yml_path.write_text("\n".join(filtered_lines), encoding="utf-8")

        # 3. Add 4th column to database
        conn = duckdb.connect(str(db_path))
        conn.execute("ALTER TABLE main.my_table ADD COLUMN email VARCHAR")
        conn.close()

        # 4. Run sync_sources
        plan2 = orchestrator.sync_sources(["main"])

        # Verify plan
        assert len(plan2.ops) == 1
        op = plan2.ops[0]
        assert isinstance(op, UpdateYamlFile)

        # The patches should include adding 'email' column and updating data_types if they changed
        # DuckDB integration might report type changes (e.g. INTEGER -> int4) depending on how it's mapped.

        # Apply plan
        orchestrator.apply_plan(plan2)

        # 5. Verify final YAML
        final_content = yml_path.read_text(encoding="utf-8")
        assert "name: email" in final_content
        assert "description: 'The unique ID'" in final_content
        assert "name: id" in final_content
        assert "name: age" in final_content

if __name__ == "__main__":
    unittest.main()
