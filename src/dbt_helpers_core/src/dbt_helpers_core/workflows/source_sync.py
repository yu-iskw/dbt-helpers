from pathlib import Path
from typing import TYPE_CHECKING, cast

from dbt_helpers_sdk import (
    CreateFile,
    DbtResourceIR,
    PatchOp,
    Plan,
    SchemaAdapter,
    UpdateYamlFile,
)

from ..resource_mapper import map_catalog_to_ir

if TYPE_CHECKING:
    from ..orchestrator import Orchestrator


class SourceSyncService:
    """Service for synchronizing dbt sources with warehouse metadata."""

    def __init__(self, orchestrator: "Orchestrator"):
        self.orch = orchestrator

    def generate_plan(self, scope: list[str]) -> Plan:
        """Generate a plan to import new sources or update existing ones."""
        # 0. Build current state
        project_state = self.orch.state_builder.build_state()

        # 1. Select Plugins
        wh_plugin = self.orch.get_warehouse_plugin()
        schema_plugin: SchemaAdapter = self.orch.get_schema_plugin()

        # 2. Read Catalog
        relations = wh_plugin.read_catalog(scope, self.orch.config.warehouse.connection)

        # 3. Map to IR and apply project aliases
        ir_resources = map_catalog_to_ir(relations, self.orch.config.project_alias_map)

        # 4. Create Plan
        plan = Plan()

        # Group resources by their target or existing path
        path_to_resources: dict[Path, list[DbtResourceIR]] = {}

        for res in ir_resources:
            extraction_meta = res.meta.get("_extraction_metadata", {})
            source_name = extraction_meta.get("source_name", "default")
            resource_id = f"{source_name}.{res.name}"

            if resource_id in project_state.sources:
                target_path = project_state.sources[resource_id]
            else:
                # Group by source_name: if any other table in this source exists, use its path
                existing_path = next(
                    (
                        path
                        for other_id, path in project_state.sources.items()
                        if other_id.startswith(f"{source_name}.")
                    ),
                    None,
                )
                if existing_path:
                    target_path = existing_path
                else:
                    target_path = Path(self.orch.path_policy.resolve_path_for_resource(res, "source"))

            full_path = self.orch.project_dir / target_path
            if full_path not in path_to_resources:
                path_to_resources[full_path] = []
            path_to_resources[full_path].append(res)

        # Generate ops per path
        for path, resources in path_to_resources.items():
            if path.exists():
                # Sync logic: calculate patches for existing resources, and add new ones
                current_content = path.read_text(encoding="utf-8")
                current_irs = schema_plugin.parse_source_yaml(current_content)

                all_patches = []
                new_resources_to_add = []

                for new_ir in resources:
                    current_ir = next((r for r in current_irs if r.name == new_ir.name), None)
                    if current_ir:
                        patches = schema_plugin.calculate_patch(current_ir, new_ir)
                        all_patches.extend(patches)
                    else:
                        new_resources_to_add.append(new_ir)

                if new_resources_to_add:
                    # Render new resources and add them to the file
                    # We might need a better way to append to YAML than just PatchOp for now
                    # For source sync, adding a new table is common.
                    for res_to_add in new_resources_to_add:
                        # Map DbtResourceIR to dict for YAML
                        res_dict = {
                            "name": res_to_add.name,
                        }
                        if res_to_add.description:
                            res_dict["description"] = res_to_add.description
                        if res_to_add.columns:
                            res_dict["columns"] = [
                                {"name": col.name, "description": col.description}
                                for col in res_to_add.columns
                            ]

                        source_name = resources[0].meta["_extraction_metadata"]["source_name"]
                        all_patches.append(PatchOp(
                            op="merge_sequence_unique",
                            path=["sources", {"name": source_name}, "tables"],
                            value=[res_dict]
                        ))

                if all_patches:
                    plan.add_op(UpdateYamlFile(path=path, patch_ops=all_patches))
            else:
                # Import logic: create new file
                source_yaml = self._render_new_source(resources, schema_plugin)
                plan.add_op(CreateFile(path=path, content=source_yaml))

        return plan

    def _render_new_source(self, resources: list[DbtResourceIR], schema_plugin: SchemaAdapter) -> str:
        from importlib.metadata import PackageNotFoundError, version  # pylint: disable=C0415
        try:
            dbt_helper_version = version("dbt-helpers")
        except PackageNotFoundError:
            dbt_helper_version = "0.1.0"

        extraction_meta = resources[0].meta.get("_extraction_metadata", {})
        source_name = extraction_meta.get("source_name", "raw")
        db_name = extraction_meta.get("database") or source_name
        project_alias = self.orch.config.project_alias_map.get(db_name, db_name)
        dataset = extraction_meta.get("schema") or source_name

        db_pattern = f"{{{{ var('databases', var('projects', {{}})).get('{project_alias}', target.database) }}}}"

        context = {
            "dbt_helper_version": dbt_helper_version,
            "project_alias": project_alias,
            "dataset": dataset,
            "owner": self.orch.config.owner,
        }

        return cast(
            "str",
            schema_plugin.render_source_yaml(
                resources,
                self.orch.config.dbt_properties.target_version,
                source_name=source_name,
                database=db_pattern,
                context=context,
            ),
        )

    def sync(self, scope: list[str]) -> Plan:
        """Sync existing sources with warehouse metadata."""
        # Now sync is just a subset of generate_plan or calls it
        return self.generate_plan(scope)
