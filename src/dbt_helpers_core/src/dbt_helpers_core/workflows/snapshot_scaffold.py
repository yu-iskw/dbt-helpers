from dbt_helpers_sdk import (
    CatalogNamespace,
    CatalogRelation,
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
        ir_resources = map_catalog_to_ir(relations)

        plan = Plan()

        for res in ir_resources:
            source_name = res.meta.get("_extraction_metadata", {}).get("source_name", "default")
            db_pattern = f"{{{{ var('databases', var('projects', {{}})).get('{source_name}', target.database) }}}}"

            dummy_rel = CatalogRelation(
                namespace=CatalogNamespace(parts=[source_name]),
                name=res.name,
                kind="table",
                columns=[],
            )

            # Resolve path
            sql_path = self.orch.project_dir / self.orch.path_policy.resolve_path(dummy_rel, "snapshot")

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
