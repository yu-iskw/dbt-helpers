import os
from pathlib import Path

import pytest

from dbt_helpers_core.orchestrator import Orchestrator

from .base import DuckDBIntegrationTestCase


@pytest.mark.parametrize("scenario_name", ["multi_schema"], indirect=True)
class TestDuckDBMultiSchema(DuckDBIntegrationTestCase):
    """Integration tests for multi-schema DuckDB projects."""

    def test_multi_schema_import(self):
        """Test that we can correctly import models from multiple schemas."""
        db_path = str(self.db_path)
        project_dir = self.tmp_path / "multi_schema_project"
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

        # Test importing from all schemas
        # In our scenario, dbt-duckdb prefixes custom schemas with the target schema (main)
        plan = orchestrator.generate_source_plan(["main", "main_staging", "main_intermediate"])

        # Should find 3 files
        create_ops = [
            op
            for op in plan.ops
            if any(s in str(op.path) for s in ["main__", "main_staging__", "main_intermediate__"])
        ]
        assert len(create_ops) == 3

        table_names = {op.path.stem for op in create_ops}
        assert "main__dim_users" in table_names
        assert "main_staging__stg_users" in table_names
        assert "main_intermediate__int_users" in table_names

        # Golden master verification
        golden_dir = Path(__file__).parent / "golden" / "multi_schema"
        golden_dir.mkdir(parents=True, exist_ok=True)

        for op in create_ops:
            golden_path = golden_dir / f"{op.path.name}"
            if os.environ.get("GENERATE_GOLDEN", "false").lower() == "true":
                golden_path.write_text(op.content, encoding="utf-8")

            if golden_path.exists():
                expected = golden_path.read_text(encoding="utf-8")
                assert op.content.strip() == expected.strip()
            else:
                pytest.fail(
                    f"Golden file not found: {golden_path}. Run with GENERATE_GOLDEN=true to create it."
                )
