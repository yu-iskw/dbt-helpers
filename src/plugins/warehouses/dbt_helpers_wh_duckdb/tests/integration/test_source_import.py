import duckdb

from dbt_helpers_core.orchestrator import Orchestrator
from dbt_helpers_sdk import CreateFile, Plan, UpdateYamlFile

from .base import DuckDBIntegrationTestCase


class TestDuckDBSourceImport(DuckDBIntegrationTestCase):
    """Test that generate_source_plan correctly identifies a new source in DuckDB."""

    def test_source_import_integration(self):
        """Test that generate_source_plan correctly identifies a new source in DuckDB."""
        db_path = str(self.db_path)

        # Setup project directory
        project_dir = self.tmp_path / "test_project"
        project_dir.mkdir()

        # Create dbt_helpers.yml
        config_file = project_dir / "dbt_helpers.yml"
        config_file.write_text(
            f"""
warehouse:
  plugin: "duckdb"
  connection:
    db_path: "{db_path}"
target_version: "dbt"
paths:
  source: "models/staging/{{{{ database }}}}/{{{{ table }}}}.yml"
""",
            encoding="utf-8",
        )

        orchestrator = Orchestrator(project_dir)

        # The dbt_duckdb_container should have 'main' schema with 'users' table
        plan = orchestrator.generate_source_plan(["main"])

        self.assertIsInstance(plan, Plan)
        # Should have at least one CreateFile op for models/staging/main/users.yml
        create_ops = [op for op in plan.ops if isinstance(op, CreateFile)]
        self.assertGreaterEqual(len(create_ops), 1)

        # Find the specific op for users
        users_op = next((op for op in create_ops if "users.yml" in str(op.path)), None)
        self.assertIsNotNone(users_op)
        self.assertTrue(str(users_op.path).endswith("models/staging/main/users.yml"))

        # Verify content contains basic expected fields
        content = users_op.content
        self.assertIn("sources:", content)
        self.assertIn("name: main", content)
        self.assertIn("name: users", content)
        self.assertIn("columns:", content)
        self.assertIn("name: id", content)
        self.assertIn("name: name", content)

    def test_source_import_comprehensive(self):
        """Test source import with multiple schemas and various data types."""
        db_path = self.tmp_path / "comprehensive.duckdb"
        conn = duckdb.connect(str(db_path))

        # Create multiple schemas
        conn.execute("CREATE SCHEMA schema_a")
        conn.execute("CREATE SCHEMA schema_b")

        # Create tables with various types in schema_a
        conn.execute("""
            CREATE TABLE schema_a.table_1 (
                id INTEGER,
                name VARCHAR,
                created_at TIMESTAMP,
                is_active BOOLEAN,
                price DECIMAL(10,2)
            )
        """)

        # Create a view in schema_a
        conn.execute("CREATE VIEW schema_a.view_1 AS SELECT * FROM schema_a.table_1")

        # Create a table in schema_b
        conn.execute("CREATE TABLE schema_b.table_2 (val DOUBLE)")

        conn.close()

        # Setup project
        project_dir = self.tmp_path / "comp_project"
        project_dir.mkdir()
        (project_dir / "dbt_helpers.yml").write_text(
            f"""
warehouse:
  plugin: "duckdb"
  connection:
    db_path: "{db_path}"
target_version: "dbt"
paths:
  source: "models/staging/{{{{ database }}}}/{{{{ table }}}}.yml"
""",
            encoding="utf-8",
        )

        orchestrator = Orchestrator(project_dir)

        # Import from both schemas
        plan = orchestrator.generate_source_plan(["schema_a", "schema_b"])

        # Should have 3 files: schema_a/table_1.yml, schema_a/view_1.yml, schema_b/table_2.yml
        self.assertEqual(len(plan.ops), 3)

        # Verify table_1
        t1_op = next(op for op in plan.ops if str(op.path).endswith("schema_a/table_1.yml"))
        self.assertIn("name: schema_a", t1_op.content)
        self.assertIn("name: table_1", t1_op.content)
        self.assertIn("name: id", t1_op.content)
        self.assertIn("name: price", t1_op.content)

        # Verify view_1
        v1_op = next(op for op in plan.ops if str(op.path).endswith("schema_a/view_1.yml"))
        self.assertIn("name: schema_a", v1_op.content)
        self.assertIn("name: view_1", v1_op.content)

        # Verify table_2
        t2_op = next(op for op in plan.ops if str(op.path).endswith("schema_b/table_2.yml"))
        self.assertIn("name: schema_b", t2_op.content)
        self.assertIn("name: table_2", t2_op.content)
        self.assertIn("name: val", t2_op.content)

    def test_source_import_idempotency(self):
        """Test that importing the same source twice results in an UpdateYamlFile."""
        db_path = self.tmp_path / "idempotency.duckdb"
        conn = duckdb.connect(str(db_path))
        conn.execute("CREATE TABLE main.users (id INTEGER)")
        conn.close()

        project_dir = self.tmp_path / "idemp_project"
        project_dir.mkdir()
        (project_dir / "dbt_helpers.yml").write_text(
            f"""
warehouse:
  plugin: "duckdb"
  connection:
    db_path: "{db_path}"
target_version: "dbt"
paths:
  source: "models/staging/{{{{ database }}}}/{{{{ table }}}}.yml"
""",
            encoding="utf-8",
        )

        orchestrator = Orchestrator(project_dir)

        # First run - should create the file
        plan1 = orchestrator.generate_source_plan(["main"])
        self.assertEqual(len(plan1.ops), 1)
        self.assertIsInstance(plan1.ops[0], CreateFile)

        # Apply the plan manually
        op = plan1.ops[0]
        op.path.parent.mkdir(parents=True, exist_ok=True)
        op.path.write_text(op.content, encoding="utf-8")

        # Second run - should result in UpdateYamlFile
        plan2 = orchestrator.generate_source_plan(["main"])
        self.assertEqual(len(plan2.ops), 1)
        self.assertIsInstance(plan2.ops[0], UpdateYamlFile)
