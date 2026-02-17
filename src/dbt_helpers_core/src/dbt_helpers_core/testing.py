import tempfile
import unittest
from pathlib import Path


class IntegrationTestCase(unittest.TestCase):
    """Base class for integration tests providing common utilities."""

    _tmp_dir_manager: tempfile.TemporaryDirectory | None = None
    tmp_path: Path

    def setUp(self) -> None:
        """Set up a temporary directory for each test."""
        super().setUp()
        self._tmp_dir_manager = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp_dir_manager.name)

    def tearDown(self) -> None:
        """Clean up the temporary directory after each test."""
        if self._tmp_dir_manager:
            self._tmp_dir_manager.cleanup()
        super().tearDown()

    def create_project(self, project_name: str, files: dict[str, str]) -> Path:
        """Helper to create a dbt project structure with specified files.

        Args:
            project_name: Name of the project directory.
            files: Dictionary mapping relative file paths to their contents.

        Returns:
            Path to the created project directory.
        """
        project_dir = self.tmp_path / project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        for rel_path, content in files.items():
            file_path = project_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

        return project_dir
