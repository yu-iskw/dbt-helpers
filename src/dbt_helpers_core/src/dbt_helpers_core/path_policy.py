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
        if len(parts) >= 2:
            variables["dataset"] = parts[1]
            variables["schema"] = parts[1]

        return variables
