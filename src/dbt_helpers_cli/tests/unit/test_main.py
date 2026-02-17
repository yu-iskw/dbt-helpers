import unittest

from typer.testing import CliRunner

from dbt_helpers_cli.main import app


class TestMain(unittest.TestCase):
    """Tests for the dbt-helpers CLI main entry point."""

    def setUp(self):
        self.runner = CliRunner()

    def test_source_import_help(self):
        result = self.runner.invoke(app, ["source", "import", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Import dbt Sources from warehouse metadata", result.output)

    def test_model_scaffold_help(self):
        result = self.runner.invoke(app, ["model", "scaffold", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Generate dbt Model scaffolds based on warehouse tables", result.output)
