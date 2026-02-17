import unittest

from dbt_helpers_core.yaml_store import YamlStore
from dbt_helpers_sdk import PatchOp


class TestYamlStore(unittest.TestCase):
    """Tests for the YamlStore class."""

    def setUp(self):
        self.store = YamlStore()

    def test_patch_preserves_comments(self):
        yaml_content = """
# Top level comment
version: 2
sources:
  - name: raw
    # Source comment
    tables:
      - name: users # inline comment
        description: Existing users table
"""
        patch_ops = [
            PatchOp(
                op="upsert_mapping_key",
                path=["sources", {"name": "raw"}, "tables", {"name": "users"}, "columns"],
                value=[],
            ),
            PatchOp(
                op="upsert_mapping_key",
                path=["sources", {"name": "raw"}, "tables", {"name": "users"}, "description"],
                value="Updated users table",
            ),
        ]

        patched = self.store.patch(yaml_content, patch_ops)

        self.assertIn("# Top level comment", patched)
        self.assertIn("# Source comment", patched)
        self.assertIn("# inline comment", patched)
        self.assertIn("description: Updated users table", patched)
        self.assertIn("columns: []", patched)

    def test_merge_sequence_unique(self):
        yaml_content = "tags: [tag1, tag2]"
        patch_ops = [PatchOp(op="merge_sequence_unique", path=["tags"], value=["tag2", "tag3"])]
        patched = self.store.patch(yaml_content, patch_ops)
        self.assertIn("tag1", patched)
        self.assertIn("tag2", patched)
        self.assertIn("tag3", patched)
        # Check that tag2 is not duplicated
        self.assertEqual(patched.count("tag2"), 1)

    def test_merge_sequence_unique_with_names(self):
        yaml_content = """
columns:
  - name: id
    description: the id
"""
        patch_ops = [
            PatchOp(
                op="merge_sequence_unique",
                path=["columns"],
                value=[{"name": "id", "description": "new desc"}, {"name": "email"}],
            )
        ]
        patched = self.store.patch(yaml_content, patch_ops)
        self.assertIn("name: id", patched)
        # Should NOT have overwritten description because we only merge if name is missing
        self.assertIn("description: the id", patched)
        self.assertIn("name: email", patched)
        self.assertEqual(patched.count("name: id"), 1)

    def test_delete_key(self):
        yaml_content = "key: val\nother: stay"
        patch_ops = [PatchOp(op="delete_key", path=["key"])]
        patched = self.store.patch(yaml_content, patch_ops)
        self.assertNotIn("key: val", patched)
        self.assertIn("other: stay", patched)

    def test_replace_content(self):
        yaml_content = "old: content"
        patch_ops = [PatchOp(op="replace_content", value="new: content")]
        patched = self.store.patch(yaml_content, patch_ops)
        self.assertIn("new: content", patched)
        self.assertNotIn("old: content", patched)


if __name__ == "__main__":
    unittest.main()
