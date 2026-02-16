from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class BasePlannedOp(BaseModel):
    op_kind: str


class CreateFile(BasePlannedOp):
    op_kind: Literal["create_file"] = "create_file"
    path: Path
    content: str


class UpdateYamlFile(BasePlannedOp):
    op_kind: Literal["update_yaml_file"] = "update_yaml_file"
    path: Path
    patch_ops: list[dict[str, Any]]


class DeleteFile(BasePlannedOp):
    op_kind: Literal["delete_file"] = "delete_file"
    path: Path


class AddDiagnostics(BasePlannedOp):
    op_kind: Literal["add_diagnostics"] = "add_diagnostics"
    level: str  # info, warning, error
    message: str


PlannedOp = CreateFile | UpdateYamlFile | DeleteFile | AddDiagnostics


class Plan(BaseModel):
    ops: list[PlannedOp] = Field(default_factory=list)

    def add_op(self, op: PlannedOp) -> None:
        self.ops.append(op)
