import os
import tempfile
import unittest
from pathlib import Path

from dbt_helpers_core.testing import IntegrationTestCase

from .conftest import _docker_available, _run_dbt_docker, _run_dbt_local


class DuckDBIntegrationTestCase(IntegrationTestCase):
    """Base class for DuckDB integration tests."""

    db_path: Path
    _static_db_path: Path | None = None

    @classmethod
    def setUpClass(cls) -> None:
        """Set up the DuckDB database once for the class."""
        super().setUpClass()

        # We simulate the session-scoped fixture logic here.
        # For simplicity in this migration, we'll run it once per class.
        # In a real project, you might want a more global cache if it's too slow.

        fixture_path = Path(__file__).parent / "fixtures" / "sample_project"

        # We need a stable temp dir for the DB file during the class run
        cls._db_temp_dir = tempfile.TemporaryDirectory()
        db_dir = Path(cls._db_temp_dir.name)
        cls.db_path = db_dir / "dev.duckdb"

        use_docker = os.environ.get("USE_DOCKER", "false").lower() == "true"

        if use_docker:
            if not _docker_available():
                # In unittest, we use skipTest
                raise unittest.SkipTest("Docker not available")

            # We need a tmp_path_factory like object. tempfile.mkdtemp works.
            class FakeFactory:
                def mktemp(self, name):
                    return Path(tempfile.mkdtemp(prefix=name))

            _run_dbt_docker(fixture_path, cls.db_path, FakeFactory())
        else:
            _run_dbt_local(fixture_path, cls.db_path, db_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up the database."""
        if hasattr(cls, "_db_temp_dir"):
            cls._db_temp_dir.cleanup()
        super().tearDownClass()
