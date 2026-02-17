from pathlib import Path

import pytest


class DuckDBIntegrationTestCase:
    """Base class for DuckDB integration tests using pytest.

    This class provides common setup for DuckDB integration tests.
    It uses pytest fixtures for temporary directories and database generation.
    """

    db_path: Path
    tmp_path: Path

    @pytest.fixture(autouse=True)
    def _setup_fixtures(self, tmp_path: Path, dbt_duckdb_container: Path):
        """Internal fixture to inject dependencies."""
        self.tmp_path = tmp_path
        self.db_path = dbt_duckdb_container

    def create_project(self, project_name: str, files: dict[str, str]) -> Path:
        """Helper to create a dbt project structure with specified files."""
        project_dir = self.tmp_path / project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        for rel_path, content in files.items():
            file_path = project_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

        return project_dir
