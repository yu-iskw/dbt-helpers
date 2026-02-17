from typing import Any

import yaml

from dbt_helpers_sdk import DbtColumnIR, DbtResourceIR, PatchOp

from ..diff_engine import calculate_resource_patch
from .base import BaseRenderer


class ModelRenderer(BaseRenderer):
    """Renderer for dbt models."""

    def render_yaml(
        self,
        resources: list[DbtResourceIR],
        target_version: str,
        database: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Render dbt resources into a model YAML string."""
        if not resources:
            return ""
        template = self.env.get_template("model.yml.j2")
        return str(
            template.render(
                resource=resources[0],
                resources=resources,
                target_version=target_version,
                database=database,
                context=context or {},
            )
        )

    def render_sql(
        self,
        resource: DbtResourceIR,
        database: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Render a dbt model SQL file."""
        source_name = resource.meta.get("_extraction_metadata", {}).get("source_name", "default")
        template = self.env.get_template("model.sql.j2")
        return str(
            template.render(
                resource=resource,
                source_name=source_name,
                database=database,
                context=context or {},
            )
        )

    def render_doc(
        self,
        resource: DbtResourceIR,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Render a dbt model documentation (Markdown) file."""
        template = self.env.get_template("model_doc.md.j2")
        return str(
            template.render(
                resource=resource,
                context=context or {},
            )
        )

    def parse_yaml(self, content: str) -> list[DbtResourceIR]:
        """Parse dbt model YAML into version-agnostic IR."""
        data = yaml.safe_load(content)
        if not data or "models" not in data:
            return []
        # Basic implementation for now
        resources = []
        for model in data["models"]:
            # Reuse logic from parse_source_yaml if possible, but for models
            config = model.get("config", {})
            meta = model.get("meta", {}) or config.get("meta", {})
            tags = model.get("tags", []) or config.get("tags", [])
            tests = model.get("data_tests", []) or model.get("tests", [])
            # Normalize tests to list of dicts
            normalized_tests: list[dict[str, Any]] = []
            for t in tests:
                if isinstance(t, str):
                    normalized_tests.append({t: {}})
                else:
                    normalized_tests.append(t)

            columns = []
            for col in model.get("columns", []):
                col_config = col.get("config", {})
                col_meta = col.get("meta", {}) or col_config.get("meta", {})
                col_tags = col.get("tags", []) or col_config.get("tags", [])
                col_tests = col.get("data_tests", []) or col_config.get("tests", [])

                # Normalize column tests
                normalized_col_tests: list[dict[str, Any]] = []
                for t in col_tests:
                    if isinstance(t, str):
                        normalized_col_tests.append({t: {}})
                    else:
                        normalized_col_tests.append(t)

                columns.append(
                    DbtColumnIR(
                        name=col["name"],
                        description=col.get("description"),
                        meta=col_meta,
                        tags=col_tags,
                        tests=normalized_col_tests,
                    )
                )

            resources.append(
                DbtResourceIR(
                    name=model["name"],
                    description=model.get("description"),
                    meta=meta,
                    tags=tags,
                    tests=normalized_tests,
                    columns=columns,
                    config=config,
                )
            )
        return resources

    def calculate_patch(self, current_ir: DbtResourceIR, new_ir: DbtResourceIR) -> list[PatchOp]:
        """Calculate a list of YAML patch operations to transform current_ir into new_ir."""
        base_path = ["models", {"name": current_ir.name}]
        return calculate_resource_patch(current_ir, new_ir, base_path)
