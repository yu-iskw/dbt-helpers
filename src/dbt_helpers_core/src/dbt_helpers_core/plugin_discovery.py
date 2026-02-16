import importlib.metadata
from typing import TypeVar

from dbt_helpers_sdk import CatalogClient, SchemaAdapter, ToolEmitter

T = TypeVar("T")


def discover_plugins(group: str, expected_type: type[T]) -> dict[str, T]:
    """Discover and instantiate plugins of a specific type registered via entry points."""
    plugins = {}
    entry_points = importlib.metadata.entry_points(group=group)
    for entry_point in entry_points:
        plugin_class = entry_point.load()
        # Instantiate the plugin
        instance = plugin_class()
        if isinstance(instance, expected_type):
            plugins[entry_point.name] = instance
    return plugins


def get_warehouse_plugins() -> dict[str, CatalogClient]:
    return discover_plugins("dbt_helpers.warehouse_plugins", CatalogClient)


def get_tool_plugins() -> dict[str, ToolEmitter]:
    return discover_plugins("dbt_helpers.tool_plugins", ToolEmitter)


def get_schema_plugins() -> dict[str, SchemaAdapter]:
    return discover_plugins("dbt_helpers.schema_plugins", SchemaAdapter)
