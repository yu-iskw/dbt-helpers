from typing import Any

from dbt_helpers_sdk import DbtResourceIR, PatchOp, SchemaAdapter

from .renderers.model import ModelRenderer
from .renderers.snapshot import SnapshotRenderer
from .renderers.source import SourceRenderer


class UnifiedDbtSchemaAdapter(SchemaAdapter):
    """Adapter for mapping between dbt YAML and internal IR."""

    def __init__(self) -> None:
        self.source_renderer = SourceRenderer()
        self.model_renderer = ModelRenderer(env=self.source_renderer.env)
        self.snapshot_renderer = SnapshotRenderer(env=self.source_renderer.env)

    def render_source_yaml(
        self,
        resources: list[DbtResourceIR],
        target_version: str,
        source_name: str = "raw",
        database: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Render dbt resources into a source YAML string."""
        return self.source_renderer.render_yaml(
            resources=resources,
            target_version=target_version,
            source_name=source_name,
            database=database,
            context=context,
        )

    def render_model_yaml(
        self,
        resources: list[DbtResourceIR],
        target_version: str,
        database: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Render dbt resources into a model YAML string."""
        return self.model_renderer.render_yaml(
            resources=resources,
            target_version=target_version,
            database=database,
            context=context,
        )

    def render_model_sql(
        self,
        resource: DbtResourceIR,
        database: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Render a dbt model SQL file."""
        return self.model_renderer.render_sql(
            resource=resource, database=database, context=context
        )

    def render_model_doc(
        self, resource: DbtResourceIR, context: dict[str, Any] | None = None
    ) -> str:
        """Render a dbt model documentation (Markdown) file."""
        return self.model_renderer.render_doc(resource=resource, context=context)

    def render_snapshot_yaml(
        self,
        resources: list[DbtResourceIR],
        target_version: str,
        database: str | None = None,
    ) -> str:
        """Render dbt snapshots into a YAML string for a specific dbt version."""
        return self.snapshot_renderer.render_yaml(
            resources=resources, target_version=target_version, database=database
        )

    def render_snapshot_sql(
        self, resource: DbtResourceIR, config: dict[str, Any], database: str | None = None
    ) -> str:
        """Render a dbt snapshot SQL file."""
        return self.snapshot_renderer.render_sql(
            resource=resource, config=config, database=database
        )

    def parse_source_yaml(self, content: str) -> list[DbtResourceIR]:
        """Parse dbt resource YAML into version-agnostic IR."""
        return self.source_renderer.parse_yaml(content)

    def parse_model_yaml(self, content: str) -> list[DbtResourceIR]:
        """Parse dbt model YAML into version-agnostic IR."""
        return self.model_renderer.parse_yaml(content)

    def calculate_patch(
        self,
        current_ir: DbtResourceIR,
        new_ir: DbtResourceIR,
    ) -> list[PatchOp]:
        """Calculate a list of YAML patch operations to transform current_ir into new_ir."""
        if "source_name" in current_ir.meta.get("_extraction_metadata", {}):
            return self.source_renderer.calculate_patch(current_ir, new_ir)
        return self.model_renderer.calculate_patch(current_ir, new_ir)
