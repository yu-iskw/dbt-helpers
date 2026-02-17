from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class WarehouseConfig(BaseModel):
    """Configuration for the warehouse plugin."""

    plugin: str
    connection: dict[str, Any] = Field(default_factory=dict)


class ProjectConfig(BaseModel):
    """Configuration for the dbt-helpers project."""

    warehouse: WarehouseConfig
    target_version: str = "fusion"  # Default to fusion
    owner: str = "data-engineering"
    project_alias_map: dict[str, str] = Field(default_factory=dict)
    paths: dict[str, str] = Field(
        default_factory=lambda: {
            "model": "models/{{ schema }}/{{ table }}.sql",
            "model_yaml": "models/{{ schema }}/{{ table }}.yml",
            "model_doc": "models/{{ schema }}/{{ table }}.md",
            "source": "models/{{ schema }}/sources.yml",
            "snapshot": "snapshots/{{ table }}.sql",
            "snapshot_yaml": "snapshots/{{ table }}.yml",
        }
    )


def load_config(path: Path) -> ProjectConfig:
    """Load the project configuration from a YAML file."""
    if not path.exists():
        # Return default config if file doesn't exist
        return ProjectConfig(warehouse=WarehouseConfig(plugin="duckdb"))
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return ProjectConfig(**data)
