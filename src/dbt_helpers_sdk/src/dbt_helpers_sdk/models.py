from typing import Any

from pydantic import BaseModel, Field


class CatalogNamespace(BaseModel):
    parts: list[str]

    def __str__(self) -> str:
        """Return a dot-separated string representation of the namespace."""
        return ".".join(self.parts)


class CatalogColumn(BaseModel):
    name: str
    data_type: str
    description: str | None = None
    nullable: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class CatalogRelation(BaseModel):
    namespace: CatalogNamespace
    name: str
    kind: str  # table, view, etc.
    columns: list[CatalogColumn]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def full_name(self) -> str:
        return f"{self.namespace}.{self.name}"
