import hashlib
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Scenario:
    """Defines a dbt project scenario for integration testing."""

    name: str
    models: dict[str, str] = field(default_factory=dict)
    seeds: dict[str, str] = field(default_factory=dict)
    project_vars: dict[str, Any] = field(default_factory=dict)
    profiles_config: dict[str, Any] = field(default_factory=dict)

    def get_hash(self, dbt_flavor: str, dbt_version: str) -> str:
        """Calculate a unique hash for this scenario and environment."""
        payload = {
            "models": self.models,
            "seeds": self.seeds,
            "project_vars": self.project_vars,
            "profiles_config": self.profiles_config,
            "dbt_flavor": dbt_flavor,
            "dbt_version": dbt_version,
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def write_to_disk(self, target_dir: Path):
        """Write the scenario to a directory as a dbt project."""
        target_dir.mkdir(parents=True, exist_ok=True)

        # Create models
        models_dir = target_dir / "models"
        models_dir.mkdir(exist_ok=True)
        for name, content in self.models.items():
            (models_dir / f"{name}.sql").write_text(content, encoding="utf-8")

        # Create seeds
        seeds_dir = target_dir / "seeds"
        seeds_dir.mkdir(exist_ok=True)
        for name, content in self.seeds.items():
            (seeds_dir / f"{name}.csv").write_text(content, encoding="utf-8")

        # Create dbt_project.yml
        project_config = {
            "name": self.name,
            "version": "1.0.0",
            "config-version": 2,
            "profile": "default",
            "model-paths": ["models"],
            "seed-paths": ["seeds"],
            "vars": self.project_vars,
        }

        with (target_dir / "dbt_project.yml").open("w", encoding="utf-8") as f:
            yaml.dump(project_config, f)

        # Create profiles.yml
        profile_config = {
            "default": {
                "outputs": {
                    "dev": {
                        "type": "duckdb",
                        "path": "dev.duckdb",
                        **self.profiles_config
                    }
                },
                "target": "dev"
            }
        }
        with (target_dir / "profiles.yml").open("w", encoding="utf-8") as f:
            yaml.dump(profile_config, f)


@dataclass(frozen=True)
class DirectoryScenario(Scenario):
    """Scenario that loads a dbt project from a directory."""

    base_path: Path = field(default_factory=Path)

    def get_hash(self, dbt_flavor: str, dbt_version: str) -> str:
        """Calculate hash based on directory content."""
        hasher = hashlib.sha256()
        # Add dbt config to hash
        hasher.update(dbt_flavor.encode())
        hasher.update(dbt_version.encode())

        # Add profile config to hash
        encoded_profile = json.dumps(self.profiles_config, sort_keys=True).encode("utf-8")
        hasher.update(encoded_profile)

        # Recursively hash files in base_path
        if self.base_path.exists():
            # Use relative paths for hashing to distinguish files with same name in different dirs
            for path in sorted(self.base_path.rglob("*")):
                if path.is_file():
                    # Check if any part of the relative path should be excluded
                    rel_path = path.relative_to(self.base_path)
                    if any(
                        p in rel_path.parts
                        for p in [".git", "target", "dbt_packages", "__pycache__", "logs"]
                    ):
                        continue

                    hasher.update(str(rel_path).encode())
                    hasher.update(path.read_bytes())

        return hasher.hexdigest()

    def write_to_disk(self, target_dir: Path):
        """Copy the directory to target_dir and inject profiles.yml."""
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(self.base_path, target_dir)

        # Ensure profiles.yml is present and points to dev.duckdb
        profile_config = {
            "default": {
                "outputs": {
                    "dev": {
                        "type": "duckdb",
                        "path": "dev.duckdb",
                        **self.profiles_config
                    }
                },
                "target": "dev"
            }
        }
        with (target_dir / "profiles.yml").open("w", encoding="utf-8") as f:
            yaml.dump(profile_config, f)


class ScenarioRegistry:
    """Registry for managing and retrieving test scenarios."""

    def __init__(self) -> None:
        self._scenarios: dict[str, Scenario] = {}

    def register(self, scenario: Scenario) -> None:
        """Register a new scenario."""
        self._scenarios[scenario.name] = scenario

    def get(self, name: str) -> Scenario:
        """Retrieve a scenario by name."""
        if name not in self._scenarios:
            raise ValueError(f"Scenario '{name}' not found in registry.")
        return self._scenarios[name]

    def list_names(self) -> list[str]:
        """List all registered scenario names."""
        return list(self._scenarios.keys())


# Global registry instance
registry = ScenarioRegistry()

# Define the default sample_project scenario
sample_project = Scenario(
    name="sample_project",
    models={
        "users": "select 1 as id, 'Alice' as name union all select 2 as id, 'Bob' as name",
        "orders": "select 1 as id, 1 as user_id, 100 as amount union all select 2 as id, 2 as user_id, 200 as amount",
    },
    project_vars={"my_var": "default_value"},
)

registry.register(sample_project)


# Scenario for testing description sync
sync_description = Scenario(
    name="sync_description",
    models={
        "users": "select 1 as id, 'Alice' as name",
    },
)

# Scenario for testing column addition
add_column = Scenario(
    name="add_column",
    models={
        "users": "select 1 as id, 'Alice' as name",
    },
)

registry.register(sync_description)
registry.register(add_column)


# Realistic jaffle_shop project
jaffle_shop = DirectoryScenario(
    name="jaffle_shop",
    base_path=Path(__file__).parent.parent / "fixtures" / "jaffle_shop",
)

registry.register(jaffle_shop)
