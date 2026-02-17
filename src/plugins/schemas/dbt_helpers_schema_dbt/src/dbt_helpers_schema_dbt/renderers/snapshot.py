from typing import Any

from dbt_helpers_sdk import DbtResourceIR

from .base import BaseRenderer


class SnapshotRenderer(BaseRenderer):
    """Renderer for dbt snapshots."""

    def render_yaml(self, resources: list[DbtResourceIR], target_version: str, database: str | None = None) -> str:
        """Render dbt snapshots into a YAML string for a specific dbt version."""
        template = self.env.get_template("snapshot.yml.j2")
        return str(template.render(resources=resources, target_version=target_version, database=database))

    def render_sql(
        self, resource: DbtResourceIR, config: dict[str, Any], database: str | None = None
    ) -> str:
        """Render a dbt snapshot SQL file."""
        template = self.env.get_template("snapshot.sql.j2")
        return str(template.render(resource=resource, config=config, database=database))
