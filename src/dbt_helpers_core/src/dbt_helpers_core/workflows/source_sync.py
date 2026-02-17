from pathlib import Path

from dbt_helpers_sdk import (
    CatalogNamespace,
    CatalogRelation,
    CreateFile,
    DbtResourceIR,
    Plan,
    UpdateYamlFile,
)

from ..resource_mapper import map_catalog_to_ir


class SourceSyncService:
    """Service for synchronizing dbt sources with warehouse metadata."""

    def __init__(self, orchestrator):
        self.orch = orchestrator

    def generate_plan(self, scope: list[str]) -> Plan:
        """Generate a plan to import new sources."""
        # 0. Build current state
        project_state = self.orch.state_builder.build_state()

        # 1. Select Plugins
        wh_plugin = self.orch.get_warehouse_plugin()
        schema_plugin = self.orch.get_schema_plugin()

        # 2. Read Catalog
        relations = wh_plugin.read_catalog(scope, self.orch.config.warehouse.connection)

        # 3. Map to IR
        ir_resources = map_catalog_to_ir(relations)

        # 4. Create Plan
        plan = Plan()

        from importlib.metadata import PackageNotFoundError, version  # pylint: disable=C0415

        try:
            dbt_helper_version = version("dbt-helpers")
        except PackageNotFoundError:
            dbt_helper_version = "0.1.0"

        # Group resources by their target or existing path
        path_to_resources: dict[Path, list[DbtResourceIR]] = {}

        for res in ir_resources:
            extraction_meta = res.meta.get("_extraction_metadata", {})
            source_name = extraction_meta.get("source_name", "default")
            db_name = extraction_meta.get("database") or source_name
            project_alias = self.orch.config.project_alias_map.get(db_name, db_name)
            dataset = extraction_meta.get("schema") or source_name
            resource_id = f"{source_name}.{res.name}"

            if resource_id in project_state.sources:
                target_path = project_state.sources[resource_id]
            else:
                # Reconstruct a dummy relation for PathPolicy
                dummy_rel = CatalogRelation(
                    namespace=CatalogNamespace(parts=[project_alias, dataset]),
                    name=res.name,
                    kind="table",
                    columns=[],
                )
                target_path = Path(self.orch.path_policy.resolve_path(dummy_rel, "source"))

            full_path = self.orch.project_dir / target_path
            if full_path not in path_to_resources:
                path_to_resources[full_path] = []
            path_to_resources[full_path].append(res)

        # Generate ops per path
        for path, resources in path_to_resources.items():
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

            source_yaml = schema_plugin.render_source_yaml(
                resources,
                self.orch.config.target_version,
                source_name=source_name,
                database=db_pattern,
                context=context,
            )

            if path.exists():
                plan.add_op(UpdateYamlFile(path=path, patch_ops=[{"content": source_yaml}]))
            else:
                plan.add_op(CreateFile(path=path, content=source_yaml))

        return plan

    def sync(self, scope: list[str]) -> Plan:
        """Sync existing sources with warehouse metadata."""
        project_state = self.orch.state_builder.build_state()
        wh_plugin = self.orch.get_warehouse_plugin()
        schema_plugin = self.orch.get_schema_plugin()

        relations = wh_plugin.read_catalog(scope, self.orch.config.warehouse.connection)
        new_ir_resources = map_catalog_to_ir(relations)

        # Group by path to avoid redundant reads
        path_to_new_irs: dict[Path, list[DbtResourceIR]] = {}
        for new_ir in new_ir_resources:
            source_name = new_ir.meta.get("_extraction_metadata", {}).get("source_name", "default")
            resource_id = f"{source_name}.{new_ir.name}"
            if resource_id in project_state.sources:
                path = project_state.sources[resource_id]
                if path not in path_to_new_irs:
                    path_to_new_irs[path] = []
                path_to_new_irs[path].append(new_ir)

        plan = Plan()
        for path, new_irs in path_to_new_irs.items():
            full_path = self.orch.project_dir / path
            if full_path.exists():
                current_content = full_path.read_text(encoding="utf-8")
                current_irs = schema_plugin.parse_source_yaml(current_content)

                all_patches = []
                for new_ir in new_irs:
                    current_ir = next((r for r in current_irs if r.name == new_ir.name), None)
                    if current_ir:
                        patches = schema_plugin.calculate_patch(current_ir, new_ir)
                        all_patches.extend(patches)

                if all_patches:
                    plan.add_op(UpdateYamlFile(path=path, patch_ops=all_patches))

        return plan
