from typing import Any, Protocol, runtime_checkable

from .dbt_resource import DbtResourceIR
from .models import CatalogRelation
from .plan import PatchOp, Plan


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

    def render_source_yaml(
        self,
        resources: list[DbtResourceIR],
        target_version: str,
        source_name: str = "raw",
        database: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Render dbt resources into a YAML string for a specific dbt version."""

    def render_model_yaml(
        self,
        resources: list[DbtResourceIR],
        target_version: str,
        database: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Render dbt models into a YAML string for a specific dbt version."""

    def render_model_sql(
        self,
        resource: DbtResourceIR,
        database: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Render a dbt model SQL file."""

    def render_model_doc(
        self,
        resource: DbtResourceIR,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Render a dbt model documentation (Markdown) file."""

    def parse_source_yaml(self, content: str) -> list[DbtResourceIR]:
        """Parse dbt resource YAML into version-agnostic IR."""

    def parse_model_yaml(self, content: str) -> list[DbtResourceIR]:
        """Parse dbt model YAML into version-agnostic IR."""

    def render_snapshot_yaml(
        self,
        resources: list[DbtResourceIR],
        target_version: str,
        database: str | None = None,
    ) -> str:
        """Render dbt snapshots into a YAML string for a specific dbt version."""

    def render_snapshot_sql(
        self, resource: DbtResourceIR, config: dict[str, Any], database: str | None = None
    ) -> str:
        """Render a dbt snapshot SQL file."""

    def calculate_patch(self, current_ir: DbtResourceIR, new_ir: DbtResourceIR) -> list[PatchOp]:
        """Calculate a list of YAML patch operations to transform current_ir into new_ir."""
