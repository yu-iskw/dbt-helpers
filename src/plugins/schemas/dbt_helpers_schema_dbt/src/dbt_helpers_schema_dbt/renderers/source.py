from typing import Any

import yaml

from dbt_helpers_sdk import DbtColumnIR, DbtResourceIR, PatchOp

from ..diff_engine import calculate_resource_patch
from .base import BaseRenderer


class SourceRenderer(BaseRenderer):
    """Renderer for dbt sources."""

    def render_yaml(
        self,
        resources: list[DbtResourceIR],
        target_version: str,
        source_name: str = "raw",
        database: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Render dbt resources into a source YAML string."""
        template = self.env.get_template("source.yml.j2")
        return str(
            template.render(
                resources=resources,
                target_version=target_version,
                source_name=source_name,
                database=database,
                context=context or {},
            )
        )

    def parse_yaml(self, content: str) -> list[DbtResourceIR]:
        """Parse dbt resource YAML into version-agnostic IR."""
        data = yaml.safe_load(content)
        resources = []

        if not data or "sources" not in data:
            return []

        for source in data["sources"]:
            source_name = source["name"]
            for table in source.get("tables", []):
                # Normalization: Look in both config and top-level
                config = table.get("config", {})
                meta = table.get("meta", {})
                if not meta:
                    meta = config.get("meta", {})

                # Flatten 'labels' if it exists in meta
                if "labels" in meta:
                    labels = meta.pop("labels")
                    if isinstance(labels, dict):
                        meta.update(labels)

                extraction_meta = {
                    "source_name": source_name,
                    "schema": source.get("schema"),
                    "database": source.get("database"),
                    "identifier": table.get("identifier"),
                }
                meta["_extraction_metadata"] = extraction_meta

                tags = table.get("tags", [])
                if not tags:
                    tags = config.get("tags", [])

                tests = table.get("data_tests", [])
                if not tests:
                    tests = table.get("tests", [])

                normalized_tests: list[dict[str, Any]] = []
                for t in tests:
                    if isinstance(t, str):
                        normalized_tests.append({t: {}})
                    else:
                        normalized_tests.append(t)

                columns = []
                for col in table.get("columns", []):
                    col_config = col.get("config", {})
                    col_meta = col.get("meta", {})
                    if not col_meta:
                        col_meta = col_config.get("meta", {})

                    col_tags = col.get("tags", [])
                    if not col_tags:
                        col_tags = col_config.get("tags", [])

                    col_tests = col.get("data_tests", [])
                    if not col_tests:
                        col_tests = col.get("tests", [])

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
                        name=table["name"],
                        description=table.get("description"),
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
        source_name = current_ir.meta.get("_extraction_metadata", {}).get("source_name", "raw")
        base_path = ["sources", {"name": source_name}, "tables", {"name": current_ir.name}]
        return calculate_resource_patch(current_ir, new_ir, base_path)
