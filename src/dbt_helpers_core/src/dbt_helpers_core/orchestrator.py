from collections.abc import Callable
from pathlib import Path
from typing import Any

from dbt_helpers_sdk import (
    Plan,
    PlannedOp,
    UpdateYamlFile,
)

from .config import ProjectConfig, load_config
from .path_policy import PathPolicy
from .plugin_discovery import get_schema_plugins, get_warehouse_plugins
from .safe_fs_writer import SafeFSWriter
from .state_builder import StateBuilder
from .workflows.model_scaffold import ModelScaffoldService
from .workflows.snapshot_scaffold import SnapshotScaffoldService
from .workflows.source_sync import SourceSyncService
from .yaml_store import YamlStore


class Orchestrator:
    """Orchestrates the catalog extraction and dbt project state building."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.config_path = project_dir / "dbt_helpers.yml"
        self._config: ProjectConfig | None = None
        self.state_builder = StateBuilder(project_dir)

        # Initialize workflow services
        self.source_sync_service = SourceSyncService(self)
        self.model_scaffold_service = ModelScaffoldService(self)
        self.snapshot_scaffold_service = SnapshotScaffoldService(self)

    @property
    def config(self) -> ProjectConfig:
        if self._config is None:
            self._config = load_config(self.config_path)
        return self._config

    @property
    def path_policy(self) -> PathPolicy:
        return PathPolicy(self.config.paths)

    def get_warehouse_plugin(self) -> Any:
        """Get the configured warehouse plugin."""
        wh_plugins = get_warehouse_plugins()
        wh_name = self.config.warehouse.plugin
        if wh_name not in wh_plugins:
            raise ValueError(f"Warehouse plugin '{wh_name}' not found. Available: {list(wh_plugins.keys())}")
        return wh_plugins[wh_name]

    def get_schema_plugin(self) -> Any:
        """Get the configured schema plugin (defaults to 'dbt')."""
        schema_plugins = get_schema_plugins()
        schema_name = self.config.dbt_properties.adapter
        if schema_name not in schema_plugins:
            raise ValueError(
                f"Schema plugin '{schema_name}' not found. Available: {list(schema_plugins.keys())}"
            )
        return schema_plugins[schema_name]

    def generate_source_plan(self, scope: list[str]) -> Plan:
        """Generate a plan to import new sources."""
        return self.source_sync_service.generate_plan(scope)

    def scaffold_models(self, scope: list[str]) -> Plan:
        """Read catalog for specified scope and generate scaffolded dbt models."""
        return self.model_scaffold_service.scaffold(scope)

    def apply_plan(self, plan: Plan, callback: Callable[[PlannedOp], None] | None = None) -> None:
        """Apply the given plan to the project using safe I/O."""
        yaml_store = YamlStore()
        fs_writer = SafeFSWriter(self.project_dir)

        for op in plan.ops:
            if callback:
                callback(op)
            if isinstance(op, UpdateYamlFile):
                # Load current content and apply patches
                full_path = self.project_dir / op.path
                if full_path.exists():
                    current_content = full_path.read_text(encoding="utf-8")
                    new_content = yaml_store.patch(current_content, op.patch_ops)
                    fs_writer.create_file(op.path, new_content)
            else:
                fs_writer.apply_op(op)

    def sync_sources(self, scope: list[str]) -> Plan:
        """Sync existing sources with warehouse metadata."""
        return self.source_sync_service.sync(scope)

    def sync_models(self, scope: list[str]) -> Plan:
        """Sync existing models with warehouse metadata."""
        return self.model_scaffold_service.sync(scope)

    def scaffold_snapshots(self, scope: list[str]) -> Plan:
        """Read catalog for specified scope and generate scaffolded dbt snapshots."""
        return self.snapshot_scaffold_service.scaffold(scope)
