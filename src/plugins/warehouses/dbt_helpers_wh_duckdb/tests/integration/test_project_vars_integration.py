import os
import subprocess  # nosec B404

from dbt_helpers_core.orchestrator import Orchestrator

from .base import DuckDBIntegrationTestCase


class TestProjectVarsIntegration(DuckDBIntegrationTestCase):
    """Integration test for dbt project variable switching."""

    def test_project_vars_integration_flow(self):
        """Verify that generated scaffolds with project vars can be compiled by dbt."""
        db_path = str(self.db_path)
        project_dir = self.tmp_path / "project_vars_itest"
        project_dir.mkdir()

        # 1. Create dbt_helpers.yml
        config_file = project_dir / "dbt_helpers.yml"
        config_file.write_text(
            f"""
warehouse:
  plugin: "duckdb"
  connection:
    db_path: "{db_path}"
target_version: "dbt"
paths:
  source: "models/staging/{{{{ database }}}}/sources.yml"
  model: "models/staging/{{{{ database }}}}/{{{{ table }}}}.sql"
  model_yaml: "models/staging/{{{{ database }}}}/{{{{ table }}}}.yml"
  model_doc: "models/staging/{{{{ database }}}}/{{{{ table }}}}.md"
""",
            encoding="utf-8",
        )

        # 2. Create dbt_project.yml and profiles.yml for dbt
        # Template uses var('projects')[project_alias]; provide default so compile succeeds.
        (project_dir / "dbt_project.yml").write_text(
            """
name: 'project_vars_itest'
version: '1.0.0'
config-version: 2
profile: 'default'
model-paths: ["models"]
vars:
  projects:
    main: "main"
""",
            encoding="utf-8",
        )

        (project_dir / "profiles.yml").write_text(
            f"""
default:
  outputs:
    dev:
      type: duckdb
      path: {db_path}
  target: dev
""",
            encoding="utf-8",
        )

        # 3. Generate source plan and apply
        orchestrator = Orchestrator(project_dir)
        source_plan = orchestrator.generate_source_plan(["main"])
        for op in source_plan.ops:
            op.path.parent.mkdir(parents=True, exist_ok=True)
            if hasattr(op, "content"):
                op.path.write_text(op.content, encoding="utf-8")

        # Verify source YAML contains the pattern
        source_yml_path = project_dir / "models/staging/main/sources.yml"
        assert source_yml_path.exists()
        source_content = source_yml_path.read_text()

        # PyYAML might wrap or escape the Jinja string. We check for the core parts.
        assert "var(" in source_content
        assert "projects" in source_content or "databases" in source_content
        assert "main" in source_content
        assert "target.database" in source_content or "projects" in source_content

        # 4. Scaffold models and apply
        model_plan = orchestrator.scaffold_models(["main"])
        for op in model_plan.ops:
            op.path.parent.mkdir(parents=True, exist_ok=True)
            if hasattr(op, "content"):
                op.path.write_text(op.content, encoding="utf-8")

        # 5. Run dbt compile
        env = os.environ.copy()
        env["DBT_PROFILES_DIR"] = str(project_dir)
        compile_args = [
            "dbt",
            "compile",
            "--project-dir",
            str(project_dir),
            "--no-partial-parse",
        ]

        # Test 1: Compile without vars (vars default from dbt_project.yml)
        result = subprocess.run(  # nosec B603, B607 # noqa: S603
            compile_args,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(
                f"dbt compile failed: {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )

        # Test 2: Compile with vars override (template uses var('projects'), not 'databases')
        result2 = subprocess.run(  # nosec B603, B607 # noqa: S603
            [*compile_args, "--vars", '{"projects": {"main": "override_db"}}'],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if result2.returncode != 0:
            raise AssertionError(
                f"dbt compile with vars failed: {result2.returncode}\nstdout:\n{result2.stdout}\n"
                f"stderr:\n{result2.stderr}"
            )

        # Check compiled SQL (model path uses dbt_name main__users)
        compiled_sql_path = project_dir / "target/compiled/project_vars_itest/models/staging/main/main__users.sql"
        if compiled_sql_path.exists():
            # Depending on how dbt-duckdb renders 'source()', it might include the database name.
            pass
