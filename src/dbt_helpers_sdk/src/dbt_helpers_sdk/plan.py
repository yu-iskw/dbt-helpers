from pathlib import Path
from typing import Any, Literal, cast

from pydantic import BaseModel, Field


class BasePlannedOp(BaseModel):
    op_kind: str


class PatchOp(BaseModel):
    op: Literal["upsert_mapping_key", "merge_sequence_unique", "delete_key", "replace_content"]
    path: list[str | int | dict[str, Any]] = Field(default_factory=list)
    value: Any = None


class CreateFile(BasePlannedOp):
    op_kind: Literal["create_file"] = "create_file"
    path: Path
    content: str


class UpdateYamlFile(BasePlannedOp):
    op_kind: Literal["update_yaml_file"] = "update_yaml_file"
    path: Path
    patch_ops: list[PatchOp]


class DeleteFile(BasePlannedOp):
    op_kind: Literal["delete_file"] = "delete_file"
    path: Path


class AddDiagnostics(BasePlannedOp):
    op_kind: Literal["add_diagnostics"] = "add_diagnostics"
    level: str  # info, warning, error
    message: str


PlannedOp = CreateFile | UpdateYamlFile | DeleteFile | AddDiagnostics


class Plan(BaseModel):
    """A collection of planned operations to be applied to a dbt project."""
    ops: list[PlannedOp] = Field(default_factory=list)

    def add_op(self, op: PlannedOp) -> None:
        self.ops.append(op)

    def to_json(self) -> str:
        """Serialize the plan to JSON."""
        return str(self.model_dump_json(indent=2))

    @classmethod
    def from_json(cls, json_str: str) -> "Plan":
        """Deserialize a plan from JSON."""
        return cast("Plan", cls.model_validate_json(json_str))

    def save(self, path: Path) -> None:
        """Save the plan to a file."""
        path.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Plan":
        """Load a plan from a file."""
        return cls.from_json(path.read_text(encoding="utf-8"))
