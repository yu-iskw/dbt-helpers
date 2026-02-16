import unittest

from dbt_helpers_core.path_policy import PathPolicy
from dbt_helpers_sdk import CatalogNamespace, CatalogRelation


class TestPathPolicy(unittest.TestCase):
    """Tests for the PathPolicy class and its path resolution logic."""

    def test_resolve_path_simple(self):
        policy = PathPolicy({"model": "models/{{ table }}.sql"})
        rel = CatalogRelation(
            namespace=CatalogNamespace(parts=["raw"]),
            name="users",
            kind="table",
            columns=[],
        )
        self.assertEqual(policy.resolve_path(rel, "model"), "models/users.sql")

    def test_resolve_path_with_schema(self):
        policy = PathPolicy({"source": "models/{{ schema }}/sources.yml"})
        rel = CatalogRelation(
            namespace=CatalogNamespace(parts=["analytics", "raw_data"]),
            name="orders",
            kind="table",
            columns=[],
        )
        # schema is alias for namespace_1
        self.assertEqual(policy.resolve_path(rel, "source"), "models/raw_data/sources.yml")

    def test_resolve_path_positional(self):
        policy = PathPolicy({"model": "models/{{ namespace_0 }}/{{ namespace_1 }}/{{ table }}.sql"})
        rel = CatalogRelation(
            namespace=CatalogNamespace(parts=["p1", "d1"]),
            name="t1",
            kind="table",
            columns=[],
        )
        self.assertEqual(policy.resolve_path(rel, "model"), "models/p1/d1/t1.sql")

    def test_resolve_path_missing_var(self):
        policy = PathPolicy({"model": "models/{{ nonexistent }}/{{ table }}.sql"})
        rel = CatalogRelation(
            namespace=CatalogNamespace(parts=["raw"]),
            name="users",
            kind="table",
            columns=[],
        )
        self.assertEqual(policy.resolve_path(rel, "model"), "models/MISSING_nonexistent/users.sql")
