import os
from pathlib import Path

import pytest

from dbt_helpers_core.orchestrator import Orchestrator
from dbt_helpers_wh_duckdb.plugin import DuckDBWarehousePlugin

from .base import DuckDBIntegrationTestCase


@pytest.mark.parametrize("scenario_name", ["complex_types"], indirect=True)
class TestDuckDBComplexTypes(DuckDBIntegrationTestCase):
    """Integration tests for complex DuckDB data types."""

    def test_complex_types_import(self):
        """Test that we can correctly import models with complex DuckDB types."""
        db_path = str(self.db_path)
        project_dir = self.tmp_path / "complex_project"
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

        # 1. Verify Catalog IR directly via plugin
        plugin = DuckDBWarehousePlugin(db_path=db_path)
        relations = plugin.read_catalog(["main"], connection_config={})

        complex_rel = next(r for r in relations if r.name == "complex_model")
        col_map = {c.name: c for c in complex_rel.columns}

        assert "STRUCT" in col_map["person_struct"].data_type
        assert col_map["int_list"].data_type == "INTEGER[]"
        assert "MAP" in col_map["string_int_map"].data_type
        assert "ENUM" in col_map["color_enum"].data_type
        assert col_map["ts"].data_type == "TIMESTAMP"
        assert col_map["dt"].data_type == "DATE"

        # 2. Verify generated YAML content
        # Find complex_model (prefixed with main__)
        complex_op = next(op for op in plan.ops if "main__complex_model" in str(op.path))
        content = complex_op.content

        # Basic assertions
        assert "name: main__complex_model" in content
        assert "columns:" in content
        assert "name: person_struct" in content
        assert "name: int_list" in content
        assert "name: string_int_map" in content
        assert "name: color_enum" in content

        # Golden master verification
        golden_dir = Path(__file__).parent / "golden" / "complex_types"
        golden_dir.mkdir(parents=True, exist_ok=True)
        golden_path = golden_dir / "main__complex_model.yml"

        if os.environ.get("GENERATE_GOLDEN", "false").lower() == "true":
            golden_path.write_text(content, encoding="utf-8")

        if golden_path.exists():
            expected = golden_path.read_text(encoding="utf-8")
            assert content.strip() == expected.strip()
        else:
            # For the first run to succeed if we haven't run with GENERATE_GOLDEN yet in this environment
            # but we want to fail if it's missing in CI
            pytest.fail(
                f"Golden file not found: {golden_path}. Run with GENERATE_GOLDEN=true to create it."
            )
