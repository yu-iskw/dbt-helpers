from pathlib import Path  # noqa: TC003

from dbt_helpers_sdk import (
    CreateFile,
    DbtResourceIR,
    Plan,
    UpdateYamlFile,
)

from ..resource_mapper import map_catalog_to_ir


class ModelScaffoldService:
    """Service for scaffolding and synchronizing dbt models."""

    def __init__(self, orchestrator):
        self.orch = orchestrator

    def scaffold(self, scope: list[str]) -> Plan:
        """Read catalog for specified scope and generate scaffolded dbt models."""
        wh_plugin = self.orch.get_warehouse_plugin()
        schema_plugin = self.orch.get_schema_plugin()

        # 2. Read Catalog
        relations = wh_plugin.read_catalog(scope, self.orch.config.warehouse.connection)

        # 3. Map to IR
        ir_resources = map_catalog_to_ir(relations, self.orch.config.project_alias_map)

        # 4. Create Plan
        plan = Plan()

        from importlib.metadata import PackageNotFoundError, version  # pylint: disable=C0415

        try:
            dbt_helper_version = version("dbt-helpers")
        except PackageNotFoundError:
            dbt_helper_version = "0.1.0"  # Fallback

        for res in ir_resources:
            extraction_meta = res.meta.get("_extraction_metadata", {})
            source_name = extraction_meta.get("source_name", "default")
            db_name = extraction_meta.get("database") or source_name
            project_alias = self.orch.config.project_alias_map.get(db_name, db_name)
            dataset = extraction_meta.get("schema") or db_name

            db_pattern = f"{{{{ var('databases', var('projects', {{}})).get('{project_alias}', target.database) }}}}"

            context = {
                "dbt_helper_version": dbt_helper_version,
                "project_alias": project_alias,
                "owner": self.orch.config.owner,
                "dataset": dataset,
                "table": res.name,
            }

            # Resolve paths
            sql_path = self.orch.project_dir / self.orch.path_policy.resolve_path_for_resource(res, "model")
            yml_path = self.orch.project_dir / self.orch.path_policy.resolve_path_for_resource(res, "model_yaml")
            doc_path = self.orch.project_dir / self.orch.path_policy.resolve_path_for_resource(res, "model_doc")

            # Generate SQL content
            sql_content = schema_plugin.render_model_sql(res, database=db_pattern, context=context)

            # Generate YAML content
            yml_content = schema_plugin.render_model_yaml(
                [res], self.orch.config.dbt_properties.target_version, database=db_pattern, context=context
            )

            # Generate Doc content
            doc_content = schema_plugin.render_model_doc(res, context=context)

            # Add Ops
            plan.add_op(CreateFile(path=sql_path, content=sql_content))
            plan.add_op(CreateFile(path=yml_path, content=yml_content))
            plan.add_op(CreateFile(path=doc_path, content=doc_content))

        return plan

    def sync(self, scope: list[str]) -> Plan:
        """Sync existing models with warehouse metadata."""
        project_state = self.orch.state_builder.build_state()
        wh_plugin = self.orch.get_warehouse_plugin()
        schema_plugin = self.orch.get_schema_plugin()

        relations = wh_plugin.read_catalog(scope, self.orch.config.warehouse.connection)
        new_ir_resources = map_catalog_to_ir(relations, self.orch.config.project_alias_map)

        path_to_new_irs: dict[Path, list[DbtResourceIR]] = {}
        for new_ir in new_ir_resources:
            if new_ir.name in project_state.models:
                path = project_state.models[new_ir.name]
                if path not in path_to_new_irs:
                    path_to_new_irs[path] = []
                path_to_new_irs[path].append(new_ir)

        plan = Plan()
        for path, new_irs in path_to_new_irs.items():
            full_path = self.orch.project_dir / path
            if full_path.exists():
                current_content = full_path.read_text(encoding="utf-8")
                current_irs = schema_plugin.parse_model_yaml(current_content)

                all_patches = []
                for new_ir in new_irs:
                    current_ir = next((r for r in current_irs if r.name == new_ir.name), None)
                    if current_ir:
                        patches = schema_plugin.calculate_patch(current_ir, new_ir)
                        all_patches.extend(patches)

                if all_patches:
                    plan.add_op(UpdateYamlFile(path=path, patch_ops=all_patches))

        return plan
