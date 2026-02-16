from typing import Any

import yaml

from dbt_helpers_sdk import DbtColumnIR, DbtResourceIR, SchemaAdapter


class UnifiedDbtSchemaAdapter(SchemaAdapter):
    """Adapter for mapping between dbt YAML and internal IR."""

    def render_source_yaml(self, resources: list[DbtResourceIR], target_version: str) -> str:
        """Render dbt resources into a source YAML string."""
        tables = [self._resource_to_dict(res, target_version) for res in resources]
        output = {
            "version": 2,
            "sources": [{"name": "raw", "tables": tables}],  # Hardcoded for MVP
        }
        out: str = yaml.dump(output, sort_keys=False, default_flow_style=False)
        return out

    def render_model_yaml(self, resources: list[DbtResourceIR], target_version: str) -> str:
        """Render dbt resources into a model YAML string."""
        models = [self._resource_to_dict(res, target_version) for res in resources]
        output = {"version": 2, "models": models}
        out: str = yaml.dump(output, sort_keys=False, default_flow_style=False)
        return out

    def _resource_to_dict(self, res: DbtResourceIR, target_version: str) -> dict[str, Any]:
        """Convert a DbtResourceIR to a dictionary suitable for YAML rendering."""
        res_dict = {
            "name": res.name,
            "description": res.description or "",
        }

        # Handle version-specific layouts
        if target_version in ["fusion", "1.11", "1.10"]:
            config = res.config.copy()
            if res.meta:
                config["meta"] = res.meta
            if res.tags:
                config["tags"] = res.tags

            if config:
                res_dict["config"] = config

            if res.tests:
                res_dict["data_tests"] = res.tests
        else:
            # Legacy / Default
            if res.meta:
                res_dict["meta"] = res.meta
            if res.tags:
                res_dict["tags"] = res.tags
            if res.tests:
                res_dict["tests"] = res.tests

        # Columns
        if res.columns:
            res_dict["columns"] = []
            for col in res.columns:
                col_dict = {
                    "name": col.name,
                    "description": col.description or "",
                }

                if target_version in ["fusion", "1.11", "1.10"]:
                    if col.tests:
                        col_dict["data_tests"] = col.tests
                    if col.meta or col.tags:
                        col_dict["config"] = {}
                        if col.meta:
                            col_dict["config"]["meta"] = col.meta
                        if col.tags:
                            col_dict["config"]["tags"] = col.tags
                else:
                    if col.meta:
                        col_dict["meta"] = col.meta
                    if col.tags:
                        col_dict["tags"] = col.tags
                    if col.tests:
                        col_dict["tests"] = col.tests

                res_dict["columns"].append(col_dict)

        return res_dict

    def parse_source_yaml(self, content: str) -> list[DbtResourceIR]:
        """Parse dbt resource YAML into version-agnostic IR."""
        data = yaml.safe_load(content)
        resources = []

        if not data or "sources" not in data:
            return []

        for source in data["sources"]:
            for table in source.get("tables", []):
                # Normalization: Look in both config and top-level
                config = table.get("config", {})
                meta = table.get("meta", {})
                if not meta:
                    meta = config.get("meta", {})

                tags = table.get("tags", [])
                if not tags:
                    tags = config.get("tags", [])

                tests = table.get("data_tests", [])
                if not tests:
                    tests = table.get("tests", [])

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

                    columns.append(
                        DbtColumnIR(
                            name=col["name"],
                            description=col.get("description"),
                            meta=col_meta,
                            tags=col_tags,
                            tests=col_tests,
                        )
                    )

                resources.append(
                    DbtResourceIR(
                        name=table["name"],
                        description=table.get("description"),
                        meta=meta,
                        tags=tags,
                        tests=tests,
                        columns=columns,
                        config=config,
                    )
                )

        return resources
