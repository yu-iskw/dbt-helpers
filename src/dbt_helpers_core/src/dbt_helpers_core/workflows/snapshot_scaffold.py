from dbt_helpers_sdk import (
    CreateFile,
    Plan,
)

from ..resource_mapper import map_catalog_to_ir


class SnapshotScaffoldService:
    """Service for scaffolding dbt snapshots."""

    def __init__(self, orchestrator):
        self.orch = orchestrator

    def scaffold(self, scope: list[str]) -> Plan:
        """Read catalog for specified scope and generate scaffolded dbt snapshots."""
        wh_plugin = self.orch.get_warehouse_plugin()
        schema_plugin = self.orch.get_schema_plugin()

        relations = wh_plugin.read_catalog(scope, self.orch.config.warehouse.connection)
        ir_resources = map_catalog_to_ir(relations, self.orch.config.project_alias_map)

        plan = Plan()

        for res in ir_resources:
            extraction_meta = res.meta.get("_extraction_metadata", {})
            source_name = extraction_meta.get("source_name", "default")
            db_name = extraction_meta.get("database") or source_name
            project_alias = self.orch.config.project_alias_map.get(db_name, db_name)

            db_pattern = f"{{{{ var('databases', var('projects', {{}})).get('{project_alias}', target.database) }}}}"

            # Resolve path
            sql_path = self.orch.project_dir / self.orch.path_policy.resolve_path_for_resource(res, "snapshot")

            # Generate Snapshot SQL content
            snapshot_config = {
                "unique_key": "id",
                "strategy": "check",
                "check_cols": "all",
                "target_schema": "snapshots",
            }

            sql_content = schema_plugin.render_snapshot_sql(
                res, snapshot_config, database=db_pattern
            )

            plan.add_op(CreateFile(path=sql_path, content=sql_content))

        return plan
