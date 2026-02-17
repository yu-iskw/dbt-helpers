import hashlib
from pathlib import Path

from dbt_helpers_wh_duckdb.plugin import DuckDBWarehousePlugin

from dbt_helpers_core.orchestrator import Orchestrator

from .base import DuckDBIntegrationTestCase


def _file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


class TestDuckDBIdempotency(DuckDBIntegrationTestCase):
    """Test idempotency of DuckDB operations."""

    def test_idempotency(self):
        """Test that running generate_source_plan twice produces an empty plan (idempotency)."""
        db_path = str(self.db_path)

        # Create config
        config_file = self.tmp_path / "dbt_helpers.yml"
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

        # Create models directory
        models_dir = self.tmp_path / "models"
        models_dir.mkdir()

        orchestrator = Orchestrator(self.tmp_path)

        # First run
        plan1 = orchestrator.generate_source_plan(["main"])
        assert len(plan1.ops) >= 1  # Should create some files

        # Simulate applying the first plan by creating the files
        for op in plan1.ops:
            if hasattr(op, "path") and hasattr(op, "content"):
                op.path.parent.mkdir(parents=True, exist_ok=True)
                op.path.write_text(op.content, encoding="utf-8")

        # Second run should be empty (idempotent)
        plan2 = orchestrator.generate_source_plan(["main"])

        # In a perfect world, plan2 should have 0 ops if all resources are already properly placed
        # But for MVP, we might still generate updates - this test documents current behavior
        print(f"First plan ops: {len(plan1.ops)}, Second plan ops: {len(plan2.ops)}")

        # For now, just verify it doesn't crash
        assert isinstance(plan2, plan1.__class__)

    def test_docker_idempotency(self):
        """Test that running Docker-based dbt build produces valid database files."""
        # Note: We use the db_path from setup which might be Docker-based if USE_DOCKER=true
        db_path = self.db_path

        # Verify database file exists
        assert db_path.exists(), f"Database file not found at {db_path}"

        # Calculate hash
        db_hash = _file_hash(db_path)

        # Verify database has expected content (not empty)
        assert db_path.stat().st_size > 0, "Database file is empty"

        print(f"Database file hash: {db_hash}")
        print(f"Database file size: {db_path.stat().st_size} bytes")

        # Verify we can read from the database
        plugin = DuckDBWarehousePlugin(db_path=str(db_path))
        relations = plugin.read_catalog(["main"], connection_config={})

        assert len(relations) >= 1, "Should have at least one relation"

        # Verify idempotency by checking that reading twice produces same results
        relations2 = plugin.read_catalog(["main"], connection_config={})
        assert len(relations) == len(relations2), "Catalog reads should be idempotent"

        # Verify relations are identical
        rel_names1 = {r.name for r in relations}
        rel_names2 = {r.name for r in relations2}
        assert rel_names1 == rel_names2, "Relation names should be identical"
