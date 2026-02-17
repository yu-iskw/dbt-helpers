"""Unit tests for BigQuery plugin."""

import unittest
from unittest.mock import MagicMock

from google.cloud.bigquery.schema import FieldElementType, SchemaField

from dbt_helpers_sdk import CatalogColumn
from dbt_helpers_wh_bigquery.plugin import (
    BigQueryWarehousePlugin,
    _map_schema_field,
    _parse_scope_item,
)


class TestParseScopeItem(unittest.TestCase):
    """Tests for _parse_scope_item."""

    def test_dot_separated_returns_project_dataset(self):
        """Scope 'proj.ds' returns (proj, ds)."""
        self.assertEqual(_parse_scope_item("proj.ds", None), ("proj", "ds"))

    def test_single_part_uses_default_project(self):
        """Scope 'ds' with default_project returns (default, ds)."""
        self.assertEqual(_parse_scope_item("ds", "my-project"), ("my-project", "ds"))

    def test_single_part_no_project_raises(self):
        """Scope 'ds' without default_project raises ValueError."""
        with self.assertRaises(ValueError):
            _parse_scope_item("ds", None)


class TestMapSchemaField(unittest.TestCase):
    """Tests for _map_schema_field."""

    def test_maps_basic_field(self):
        """Maps name, type, nullable from SchemaField."""
        field = MagicMock()
        field.name = "id"
        field.field_type = "INT64"
        field.mode = "REQUIRED"
        field.description = "Primary key"
        field.policy_tags = None
        col = _map_schema_field(field)
        self.assertIsInstance(col, CatalogColumn)
        self.assertEqual(col.name, "id")
        self.assertEqual(col.data_type, "INT64")
        self.assertFalse(col.nullable)
        self.assertEqual(col.description, "Primary key")

    def test_nullable_when_not_required(self):
        """Nullable is True when mode is not REQUIRED."""
        field = MagicMock()
        field.name = "x"
        field.field_type = "STRING"
        field.mode = "NULLABLE"
        field.description = None
        field.policy_tags = None
        col = _map_schema_field(field)
        self.assertTrue(col.nullable)


class TestMapToSqlType(unittest.TestCase):
    """Unit tests for _map_to_sql_type via _map_schema_field."""

    def test_scalar_types_passthrough(self):
        """Scalar types pass through unchanged."""
        scalar_types = (
            "STRING", "BYTES", "INT64", "FLOAT64", "BOOL", "TIMESTAMP",
            "DATE", "TIME", "DATETIME", "GEOGRAPHY", "JSON", "INTERVAL",
        )
        for ftype in scalar_types:
            field = SchemaField("x", ftype, mode="NULLABLE")
            col = _map_schema_field(field)
            self.assertEqual(col.data_type, ftype, msg=f"Expected {ftype}")

    def test_sdk_normalization(self):
        """SDK types INTEGER, FLOAT, BOOLEAN, RECORD map to INT64, FLOAT64, BOOL, STRUCT."""
        field = SchemaField("i", "INTEGER", mode="NULLABLE")
        self.assertEqual(_map_schema_field(field).data_type, "INT64")
        field = SchemaField("f", "FLOAT", mode="NULLABLE")
        self.assertEqual(_map_schema_field(field).data_type, "FLOAT64")
        field = SchemaField("b", "BOOLEAN", mode="NULLABLE")
        self.assertEqual(_map_schema_field(field).data_type, "BOOL")
        field = SchemaField("r", "RECORD", mode="NULLABLE", fields=[SchemaField("a", "INT64", mode="NULLABLE")])
        self.assertEqual(_map_schema_field(field).data_type, "STRUCT<a INT64>")

    def test_parameterized_string(self):
        """STRING(max_length) maps correctly."""
        field = SchemaField("s", "STRING", mode="NULLABLE", max_length=10)
        self.assertEqual(_map_schema_field(field).data_type, "STRING(10)")

    def test_parameterized_bytes(self):
        """BYTES(max_length) maps correctly."""
        field = SchemaField("b", "BYTES", mode="NULLABLE", max_length=10)
        self.assertEqual(_map_schema_field(field).data_type, "BYTES(10)")

    def test_parameterized_numeric(self):
        """NUMERIC(precision, scale) and BIGNUMERIC map correctly."""
        field = SchemaField("n", "NUMERIC", mode="NULLABLE", precision=10, scale=2)
        self.assertEqual(_map_schema_field(field).data_type, "NUMERIC(10, 2)")
        field = SchemaField("bn", "BIGNUMERIC", mode="NULLABLE", precision=20, scale=5)
        self.assertEqual(_map_schema_field(field).data_type, "BIGNUMERIC(20, 5)")

    def test_struct_nested(self):
        """STRUCT with nested fields maps recursively."""
        field = SchemaField(
            "rec",
            "RECORD",
            mode="NULLABLE",
            fields=[
                SchemaField("sub_int", "INT64", mode="NULLABLE"),
                SchemaField("sub_str", "STRING", mode="NULLABLE"),
            ],
        )
        self.assertEqual(_map_schema_field(field).data_type, "STRUCT<sub_int INT64, sub_str STRING>")

    def test_array_of_string(self):
        """REPEATED STRING maps to ARRAY<STRING>."""
        field = SchemaField("arr", "STRING", mode="REPEATED")
        self.assertEqual(_map_schema_field(field).data_type, "ARRAY<STRING>")

    def test_array_of_struct(self):
        """REPEATED RECORD maps to ARRAY<STRUCT<...>>."""
        field = SchemaField(
            "coords",
            "RECORD",
            mode="REPEATED",
            fields=[
                SchemaField("x", "FLOAT64", mode="NULLABLE"),
                SchemaField("y", "FLOAT64", mode="NULLABLE"),
            ],
        )
        self.assertEqual(_map_schema_field(field).data_type, "ARRAY<STRUCT<x FLOAT64, y FLOAT64>>")

    def test_range_date(self):
        """RANGE with element type maps correctly."""
        field = SchemaField("r", "RANGE", mode="NULLABLE", range_element_type=FieldElementType("DATE"))
        self.assertEqual(_map_schema_field(field).data_type, "RANGE<DATE>")


class TestBigQueryPlugin(unittest.TestCase):
    """Tests for BigQueryWarehousePlugin."""

    def test_plugin_implements_catalog_client(self):
        """Plugin can be instantiated."""
        plugin = BigQueryWarehousePlugin()
        self.assertIsNotNone(plugin)
