import unittest

from dbt_helpers_sdk.dbt_resource import DbtColumnIR, DbtResourceIR
from dbt_helpers_sdk.models import CatalogColumn, CatalogNamespace, CatalogRelation


class TestModels(unittest.TestCase):
    """Tests for the SDK data models and intermediate representation (IR) types."""

    def test_catalog_namespace_str(self):
        namespace = CatalogNamespace(parts=["project", "dataset"])
        self.assertEqual(str(namespace), "project.dataset")

    def test_catalog_relation_full_name(self):
        namespace = CatalogNamespace(parts=["project", "dataset"])
        relation = CatalogRelation(namespace=namespace, name="my_table", kind="table", columns=[])
        self.assertEqual(relation.full_name, "project.dataset.my_table")

    def test_catalog_column_defaults(self):
        column = CatalogColumn(name="id", data_type="INTEGER")
        self.assertTrue(column.nullable)
        self.assertEqual(column.metadata, {})

    def test_dbt_column_ir_defaults(self):
        column = DbtColumnIR(name="id")
        self.assertIsNone(column.description)
        self.assertEqual(column.meta, {})
        self.assertEqual(column.tags, [])
        self.assertEqual(column.tests, [])

    def test_dbt_resource_ir_defaults(self):
        resource = DbtResourceIR(name="my_model")
        self.assertIsNone(resource.description)
        self.assertEqual(resource.meta, {})
        self.assertEqual(resource.tags, [])
        self.assertEqual(resource.tests, [])
        self.assertEqual(resource.columns, [])
        self.assertEqual(resource.config, {})
