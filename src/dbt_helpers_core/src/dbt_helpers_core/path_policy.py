import re
from typing import Any

from dbt_helpers_sdk import CatalogRelation


class PathPolicy:
    """Manages the resolution of file paths based on dbt resource metadata and templates."""

    def __init__(self, templates: dict[str, str]):
        """Initialize with a dictionary of templates per resource kind.

        Example: {'model': 'models/{{ schema }}/{{ table }}.sql', 'source': 'models/{{ schema }}/sources.yml'}.
        """
        self.templates = templates

    def resolve_path(self, relation: CatalogRelation, resource_kind: str) -> str:
        template = self.templates.get(resource_kind)
        if not template:
            # Fallback or error? Let's use a safe default for now
            template = f"{resource_kind}s/{{{{ table }}}}.sql"

        variables = self._extract_variables(relation)
        return self._render(template, variables)

    def resolve_path_for_resource(self, resource: Any, resource_kind: str) -> str:
        """Resolve path using DbtResourceIR."""
        template = self.templates.get(resource_kind)
        if not template:
            template = f"{resource_kind}s/{{{{ table }}}}.sql"

        # Extract variables from IR
        meta = resource.meta.get("_extraction_metadata", {})
        variables = {
            "table": resource.name,
            "identifier": meta.get("identifier", resource.name),
            "kind": meta.get("kind", "table"),
        }

        # Use namespace_parts if available, otherwise fallback to old behavior
        parts = meta.get("namespace_parts", [])
        if parts:
            for i, part in enumerate(parts):
                variables[f"namespace_{i}"] = part
            if len(parts) >= 1:
                variables["project"] = parts[0]
                variables["database"] = parts[0]
                # Default dataset/schema to the last part if only one part exists
                variables["dataset"] = parts[-1]
                variables["schema"] = parts[-1]
            if len(parts) >= 2:
                variables["dataset"] = parts[1]
                variables["schema"] = parts[1]
        else:
            # Fallback for older metadata
            source_name = meta.get("source_name")
            if source_name:
                variables["schema"] = source_name
                variables["dataset"] = source_name

            database = meta.get("database")
            if database:
                variables["database"] = database
                variables["project"] = database

        return self._render(template, variables)

    def _render(self, template: str, variables: dict[str, Any]) -> str:
        # Simple regex substitution for {{ variable }}
        def replace(match):
            var_name = match.group(1).strip()
            return str(variables.get(var_name, f"MISSING_{var_name}"))

        return re.sub(r"\{\{\s*(\w+)\s*\}\}", replace, template)

    def _extract_variables(self, relation: CatalogRelation) -> dict[str, Any]:
        parts = relation.namespace.parts
        variables = {
            "table": relation.name,
            "identifier": relation.name,
            "kind": relation.kind,
        }

        # Positional namespace parts
        for i, part in enumerate(parts):
            variables[f"namespace_{i}"] = part

        # Common aliases
        if len(parts) >= 1:
            variables["project"] = parts[0]
            variables["database"] = parts[0]
            variables["dataset"] = parts[-1]
            variables["schema"] = parts[-1]
        if len(parts) >= 2:
            variables["dataset"] = parts[1]
            variables["schema"] = parts[1]

        return variables
