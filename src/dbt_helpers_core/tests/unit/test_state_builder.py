import shutil
import tempfile
import unittest
from pathlib import Path

from dbt_helpers_core.state_builder import StateBuilder


class TestStateBuilder(unittest.TestCase):
    """Tests for the StateBuilder class and project state scanning."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_state_builder_empty(self):
        builder = StateBuilder(self.test_dir)
        state = builder.build_state()
        self.assertEqual(len(state.models), 0)
        self.assertEqual(len(state.sources), 0)

    def test_state_builder_with_files(self):
        models_dir = self.test_dir / "models"
        models_dir.mkdir()

        # Add a model SQL file
        (models_dir / "my_model.sql").write_text("select 1")

        # Add a source YAML file
        source_yml = """
sources:
  - name: raw
    tables:
      - name: users
      - name: orders
"""
        (models_dir / "sources.yml").write_text(source_yml)

        builder = StateBuilder(self.test_dir)
        state = builder.build_state()

        self.assertIn("my_model", state.models)
        self.assertEqual(state.models["my_model"], Path("models/my_model.sql"))

        self.assertIn("raw.users", state.sources)
        self.assertEqual(state.sources["raw.users"], Path("models/sources.yml"))
        self.assertIn("raw.orders", state.sources)
        self.assertEqual(state.sources["raw.orders"], Path("models/sources.yml"))

    def test_state_builder_nested(self):
        models_dir = self.test_dir / "models" / "staging"
        models_dir.mkdir(parents=True)

        (models_dir / "stg_users.sql").write_text("select * from {{ source('raw', 'users') }}")

        builder = StateBuilder(self.test_dir)
        state = builder.build_state()

        self.assertIn("stg_users", state.models)
        self.assertEqual(state.models["stg_users"], Path("models/staging/stg_users.sql"))
