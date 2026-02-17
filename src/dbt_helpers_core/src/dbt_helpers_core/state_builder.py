from pathlib import Path

import ruamel.yaml
from pydantic import BaseModel, Field


class ProjectState(BaseModel):
    """Represents the current state of a dbt project."""

    # Map of resource_name -> path (for models)
    models: dict[str, Path] = Field(default_factory=dict)
    # Map of "source_name.table_name" -> path (for sources)
    sources: dict[str, Path] = Field(default_factory=dict)


class StateBuilder:
    """Builds the ProjectState by scanning the dbt project directory."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.yaml = ruamel.yaml.YAML(typ="safe")

    def build_state(self) -> ProjectState:
        """Scan the project directory and return a ProjectState object."""
        state = ProjectState()

        # Scan models directory (or root if needed, but dbt convention is models/)
        models_dir = self.project_dir / "models"
        if not models_dir.exists():
            return state

        for file_path in models_dir.rglob("*"):
            if file_path.suffix == ".sql":
                # filename is model name
                model_name = file_path.stem
                state.models[model_name] = file_path.relative_to(self.project_dir)
            elif file_path.suffix in (".yml", ".yaml"):
                self._parse_yaml_state(file_path, state)

        return state

    def _parse_yaml_state(self, file_path: Path, state: ProjectState):
        """Parse a YAML file and update the state with discovered resources."""
        try:
            with file_path.open(encoding="utf-8") as f:
                data = self.yaml.load(f)

            if not data:
                return

            # Parse sources
            if "sources" in data:
                for source in data["sources"]:
                    source_name = source.get("name")
                    if not source_name:
                        continue
                    for table in source.get("tables", []):
                        table_name = table.get("name")
                        if table_name:
                            key = f"{source_name}.{table_name}"
                            state.sources[key] = file_path.relative_to(self.project_dir)

            # Parse model patches
            if "models" in data:
                for model in data["models"]:
                    model_name = model.get("name")
                    if model_name and model_name not in state.models:
                        # We prioritize .sql files for model locations,
                        # but .yml might contain the schema definition
                        state.models[model_name] = file_path.relative_to(self.project_dir)

        except Exception:  # pylint: disable=broad-exception-caught
            # Skip invalid YAML files or inaccessible files for now
            return
