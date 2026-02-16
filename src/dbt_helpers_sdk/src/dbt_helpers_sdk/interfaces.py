from typing import Any, Protocol, runtime_checkable

from .dbt_resource import DbtResourceIR
from .models import CatalogRelation
from .plan import Plan


@runtime_checkable
class CatalogClient(Protocol):
    """Protocol for reading catalog metadata from a warehouse."""

    def read_catalog(self, scope: list[str], connection_config: dict[str, Any]) -> list[CatalogRelation]:
        """Read catalog metadata for the given scope."""


@runtime_checkable
class ToolEmitter(Protocol):
    """Protocol for generating a plan based on catalog metadata."""

    def emit(self, catalog: list[CatalogRelation]) -> Plan:
        """Generate a plan for the given catalog."""


@runtime_checkable
class SchemaAdapter(Protocol):
    """Protocol for mapping between dbt YAML and internal IR."""

    def render_source_yaml(self, resources: list[DbtResourceIR], target_version: str) -> str:
        """Render dbt resources into a YAML string for a specific dbt version."""

    def render_model_yaml(self, resources: list[DbtResourceIR], target_version: str) -> str:
        """Render dbt models into a YAML string for a specific dbt version."""

    def parse_source_yaml(self, content: str) -> list[DbtResourceIR]:
        """Parse dbt resource YAML into version-agnostic IR."""
