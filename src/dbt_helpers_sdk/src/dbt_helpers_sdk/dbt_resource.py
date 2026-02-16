from typing import Any

from pydantic import BaseModel, Field


class DbtColumnIR(BaseModel):
    name: str
    description: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    tests: list[dict[str, Any]] = Field(default_factory=list)


class DbtResourceIR(BaseModel):
    name: str
    description: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    tests: list[dict[str, Any]] = Field(default_factory=list)
    columns: list[DbtColumnIR] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
