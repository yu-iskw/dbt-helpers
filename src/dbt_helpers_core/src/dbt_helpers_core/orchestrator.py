from pathlib import Path

from dbt_helpers_sdk import (
    CatalogNamespace,
    CatalogRelation,
    CreateFile,
    DbtColumnIR,
    DbtResourceIR,
    Plan,
    UpdateYamlFile,
)

from .config import ProjectConfig, load_config
from .path_policy import PathPolicy
from .plugin_discovery import get_schema_plugins, get_warehouse_plugins
from .state_builder import StateBuilder


class Orchestrator:
    """Orchestrates the catalog extraction and dbt project state building."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.config_path = project_dir / "dbt_helpers.yml"
        self._config: ProjectConfig | None = None
        self.state_builder = StateBuilder(project_dir)

    @property
    def config(self) -> ProjectConfig:
        if self._config is None:
            self._config = load_config(self.config_path)
        return self._config

    @property
    def path_policy(self) -> PathPolicy:
        return PathPolicy(self.config.paths)

    def _map_catalog_to_ir(self, relations: list[CatalogRelation]) -> list[DbtResourceIR]:
        ir_resources = []
        for rel in relations:
            columns = [
                DbtColumnIR(
                    name=col.name,
                    description=col.description,
                    meta=col.metadata.get("meta", {}),
                    tags=col.metadata.get("tags", []),
                )
                for col in rel.columns
            ]

            # For sources, we often want the 'source_name' as part of IR or metadata
            # In this MVP, we'll put it in metadata so the Emitter/Adapter can use it
            metadata = rel.metadata.copy()
            if len(rel.namespace.parts) >= 1:
                metadata["source_name"] = rel.namespace.parts[-1]  # assume last part is source name

            ir_resources.append(
                DbtResourceIR(
                    name=rel.name,
                    description=rel.metadata.get("description"),
                    columns=columns,
                    meta=rel.metadata.get("meta", {}),
                    tags=rel.metadata.get("tags", []),
                    config=rel.metadata.get("config", {}),
                )
            )
            # Tag the last resource with our extracted metadata
            ir_resources[-1].meta["_extraction_metadata"] = metadata

        return ir_resources

    def generate_source_plan(self, scope: list[str]) -> Plan:
        # 0. Build current state
        project_state = self.state_builder.build_state()

        # 1. Discover Plugins
        wh_plugins = get_warehouse_plugins()
        schema_plugins = get_schema_plugins()

        # 2. Select Plugins
        wh_name = self.config.warehouse.plugin
        if wh_name not in wh_plugins:
            raise ValueError(f"Warehouse plugin '{wh_name}' not found. Available: {list(wh_plugins.keys())}")
        wh_plugin = wh_plugins[wh_name]

        schema_name = "dbt"
        if schema_name not in schema_plugins:
            raise ValueError(f"Schema plugin '{schema_name}' not found. Available: {list(schema_plugins.keys())}")
        schema_plugin = schema_plugins[schema_name]

        # 3. Read Catalog
        relations = wh_plugin.read_catalog(scope, self.config.warehouse.connection)

        # 4. Map to IR
        ir_resources = self._map_catalog_to_ir(relations)

        # 5. Create Plan
        plan = Plan()

        # Group resources by their target or existing path
        path_to_resources: dict[Path, list[DbtResourceIR]] = {}

        for res in ir_resources:
            source_name = res.meta.get("_extraction_metadata", {}).get("source_name", "default")
            resource_id = f"{source_name}.{res.name}"

            if resource_id in project_state.sources:
                target_path = project_state.sources[resource_id]
            else:
                # Use PathPolicy for new resources
                # We need the original relation to resolve variables,
                # but for MVP let's assume we can reconstruct enough from IR metadata
                # In a real app, PathPolicy might take the Relation directly.

                # Reconstruct a dummy relation for PathPolicy
                dummy_rel = CatalogRelation(
                    namespace=CatalogNamespace(parts=[source_name]),
                    name=res.name,
                    kind="table",
                    columns=[],
                )
                target_path = Path(self.path_policy.resolve_path(dummy_rel, "source"))

            full_path = self.project_dir / target_path
            if full_path not in path_to_resources:
                path_to_resources[full_path] = []
            path_to_resources[full_path].append(res)

        # Generate ops per path
        for path, resources in path_to_resources.items():
            # Get source name from the first resource (they are grouped by path, which usually means same source)
            source_name = resources[0].meta.get("_extraction_metadata", {}).get("source_name", "raw")

            # Construct the environment switching pattern for database
            db_pattern = f"{{{{ var('databases', var('projects', {{}})).get('{source_name}', target.database) }}}}"

            source_yaml = schema_plugin.render_source_yaml(
                resources,
                self.config.target_version,
                source_name=source_name,
                database=db_pattern
            )

            if path.exists():
                # In a real app, we'd only patch if content actually changes
                plan.add_op(UpdateYamlFile(path=path, patch_ops=[{"content": source_yaml}]))
            else:
                plan.add_op(CreateFile(path=path, content=source_yaml))

        return plan

    def scaffold_models(self, scope: list[str]) -> Plan:
        """Read catalog for specified scope and generate scaffolded dbt models.

        Generates both .sql (SELECT from source) and .yml (properties) files.
        """
        # 1. Discover Plugins
        wh_plugins = get_warehouse_plugins()
        schema_plugins = get_schema_plugins()

        wh_name = self.config.warehouse.plugin
        wh_plugin = wh_plugins[wh_name]
        schema_plugin = schema_plugins["dbt"]

        # 2. Read Catalog
        relations = wh_plugin.read_catalog(scope, self.config.warehouse.connection)

        # 3. Map to IR
        ir_resources = self._map_catalog_to_ir(relations)

        # 4. Create Plan
        plan = Plan()

        for res in ir_resources:
            source_name = res.meta.get("_extraction_metadata", {}).get("source_name", "default")

            # Reconstruct relation for PathPolicy
            dummy_rel = CatalogRelation(
                namespace=CatalogNamespace(parts=[source_name]),
                name=res.name,
                kind="table",
                columns=[],
            )

            # Resolve paths
            sql_path = self.project_dir / self.path_policy.resolve_path(dummy_rel, "model")
            yml_path = self.project_dir / self.path_policy.resolve_path(dummy_rel, "model_yaml")

            # Generate SQL content
            # Simple template for MVP
            sql_content = (
                "with source as (\n"
                f"    select * from {{{{ source('{source_name}', '{res.name}') }}}}\n"  # nosec B608
                ")\n"
                "select * from source\n"
            )

            # Generate YAML content
            yml_content = schema_plugin.render_model_yaml([res], self.config.target_version)

            # Add Ops
            plan.add_op(CreateFile(path=sql_path, content=sql_content))
            plan.add_op(CreateFile(path=yml_path, content=yml_content))

        return plan
