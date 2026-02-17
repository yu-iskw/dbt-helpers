import unittest

from dbt_helpers_schema_dbt.adapter import UnifiedDbtSchemaAdapter

from dbt_helpers_sdk import DbtResourceIR


class TestDbtSchemaAdapter(unittest.TestCase):
    """Tests for UnifiedDbtSchemaAdapter (Facade)."""

    def test_adapter_initialization(self):
        """Test that the adapter initializes its renderers."""
        adapter = UnifiedDbtSchemaAdapter()
        self.assertIsNotNone(adapter.source_renderer)
        self.assertIsNotNone(adapter.model_renderer)
        self.assertIsNotNone(adapter.snapshot_renderer)

    def test_adapter_delegation_source(self):
        """Test that the adapter delegates to source_renderer."""
        adapter = UnifiedDbtSchemaAdapter()
        resource = DbtResourceIR(name="test_table")
        # We don't need to verify full content here, just that it doesn't crash
        # and returns something that looks like dbt YAML.
        yaml_content = adapter.render_source_yaml([resource], target_version="fusion")
        self.assertIn("sources:", yaml_content)
        self.assertIn("test_table", yaml_content)

    def test_adapter_delegation_model(self):
        """Test that the adapter delegates to model_renderer."""
        adapter = UnifiedDbtSchemaAdapter()
        resource = DbtResourceIR(name="test_model")
        yaml_content = adapter.render_model_yaml([resource], target_version="fusion")
        self.assertIn("models:", yaml_content)
        self.assertIn("test_model", yaml_content)

    def test_adapter_delegation_snapshot(self):
        """Test that the adapter delegates to snapshot_renderer."""
        adapter = UnifiedDbtSchemaAdapter()
        resource = DbtResourceIR(name="test_snapshot")
        yaml_content = adapter.render_snapshot_yaml([resource], target_version="fusion")
        self.assertIn("snapshots:", yaml_content)
        self.assertIn("test_snapshot", yaml_content)
