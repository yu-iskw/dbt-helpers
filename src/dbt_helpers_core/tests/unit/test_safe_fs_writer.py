import json

from dbt_helpers_core.safe_fs_writer import SafeFSWriter
from dbt_helpers_core.testing import IntegrationTestCase


class TestSafeFSWriter(IntegrationTestCase):
    """Tests for the SafeFSWriter class."""

    def setUp(self):
        super().setUp()
        self.project_dir = self.create_project("test_project", {})
        self.writer = SafeFSWriter(self.project_dir)

    def test_create_file_atomic(self):
        path = self.project_dir / "new_file.sql"
        content = "select 1"

        self.writer.create_file(path, content)

        self.assertTrue(path.exists())
        self.assertEqual(path.read_text(), content)

        # Check audit log
        audit_log = self.project_dir / ".dbt_helpers" / "audit.jsonl"
        self.assertTrue(audit_log.exists())

        logs = [json.loads(line) for line in audit_log.read_text().splitlines()]
        self.assertEqual(logs[0]["op_kind"], "create")
        self.assertEqual(logs[0]["path"], str(path))

    def test_update_file_takes_backup(self):
        path = self.project_dir / "existing.sql"
        path.write_text("old content")

        self.writer.create_file(path, "new content")

        self.assertEqual(path.read_text(), "new content")

        # Check backup
        backup_dir = self.project_dir / ".dbt_helpers" / "backups"
        self.assertTrue(backup_dir.exists())
        backups = list(backup_dir.glob("*.bak"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "old content")

    def test_delete_file_takes_backup(self):
        path = self.project_dir / "to_delete.sql"
        path.write_text("delete me")

        self.writer.delete_file(path)

        self.assertFalse(path.exists())

        # Check backup
        backup_dir = self.project_dir / ".dbt_helpers" / "backups"
        backups = list(backup_dir.glob("*.bak"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "delete me")


if __name__ == "__main__":
    import unittest

    unittest.main()
