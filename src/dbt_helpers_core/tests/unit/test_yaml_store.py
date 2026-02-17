import unittest

from dbt_helpers_core.yaml_store import YamlStore


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
            {"op": "ensure_mapping_key", "path": ["sources", 0, "tables", 0, "columns"], "value": []},
            {"op": "set_scalar", "path": ["sources", 0, "tables", 0, "description"], "value": "Updated users table"},
        ]

        # Note: ruamel might handle list indexing differently if we are not careful
        # But for this MVP, we assume path can contain integers for list indexing
        # Let's adjust _ensure_mapping_key and others to handle int keys if needed
        # Or just use source name lookup logic in orchestrator and pass exact path here.

        # Actually, dbt YAMLs are usually lists of mappings.
        # Using index 0 is risky if the order changes, but for testing it's fine.

        patched = self.store.patch(yaml_content, patch_ops)

        self.assertIn("# Top level comment", patched)
        self.assertIn("# Source comment", patched)
        self.assertIn("# inline comment", patched)
        self.assertIn("description: Updated users table", patched)
        self.assertIn("columns: []", patched)

    def test_merge_sequence_unique(self):
        yaml_content = "tags: [tag1, tag2]"
        patch_ops = [{"op": "merge_sequence_unique", "path": ["tags"], "value": ["tag2", "tag3"]}]
        patched = self.store.patch(yaml_content, patch_ops)
        self.assertIn("tag1", patched)
        self.assertIn("tag2", patched)
        self.assertIn("tag3", patched)
        # Check that tag2 is not duplicated
        self.assertEqual(patched.count("tag2"), 1)


if __name__ == "__main__":
    unittest.main()
