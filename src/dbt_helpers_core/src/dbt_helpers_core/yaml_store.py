from io import StringIO
from typing import Any

from ruamel.yaml import YAML


class YamlStore:
    """Subsystem for non-destructive YAML manipulation."""

    def __init__(self):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.indent(mapping=2, sequence=4, offset=2)
        self.yaml.width = 4096  # Avoid wrapping long lines

    def load(self, content: str) -> Any:
        """Load YAML content preserving comments and order."""
        return self.yaml.load(content)

    def dump(self, data: Any) -> str:
        """Dump YAML data to string preserving comments and order."""
        stream = StringIO()
        self.yaml.dump(data, stream)
        return stream.getvalue()

    def patch(self, content: str, patch_ops: list[dict[str, Any]]) -> str:
        """Apply a series of patch operations to YAML content.

        Supported operations:
        - ensure_mapping_key: { "op": "ensure_mapping_key", "path": ["key1", "key2"], "value": {} }
        - set_scalar: { "op": "set_scalar", "path": ["key1", "key2"], "value": "new_val" }
        - merge_sequence_unique: { "op": "merge_sequence_unique", "path": ["key1", "key2"], "value": ["val1"] }
        """
        data = self.load(content)

        for op_req in patch_ops:
            op = op_req.get("op")
            path = op_req.get("path", [])
            value = op_req.get("value")

            if op == "ensure_mapping_key":
                self._ensure_mapping_key(data, path, value)
            elif op == "set_scalar":
                self._set_scalar(data, path, value)
            elif op == "merge_sequence_unique":
                if isinstance(value, list):
                    self._merge_sequence_unique(data, path, value)
            # Add more ops as needed (e.g., upsert_list_of_mappings)
            elif op == "replace_content":
                # Special case where we just replace the whole thing if it's simpler
                # but this defeats the purpose of ruamel if not careful
                data = self.load(op_req.get("content", ""))

        return self.dump(data)

    def _ensure_mapping_key(self, data: Any, path: list[str | int], default_value: Any) -> None:
        curr = data
        for i, key in enumerate(path):
            if i == len(path) - 1:
                if isinstance(curr, dict):
                    if key not in curr:
                        curr[key] = default_value
                elif isinstance(curr, list) and isinstance(key, int):
                    # For lists, we usually don't 'ensure' a key by index like this
                    # unless we want to pad the list, which is rare for YAML patching.
                    # Usually we'd use set_scalar or just append.
                    pass
            else:
                if isinstance(curr, dict):
                    if key not in curr:
                        curr[key] = {}
                    curr = curr[key]
                elif isinstance(curr, list) and isinstance(key, int):
                    curr = curr[key]

    def _set_scalar(self, data: Any, path: list[str | int], value: Any) -> None:
        curr = data
        for i, key in enumerate(path):
            if i == len(path) - 1:
                curr[key] = value
            else:
                if isinstance(curr, dict):
                    if key not in curr:
                        curr[key] = {}
                    curr = curr[key]
                elif isinstance(curr, list) and isinstance(key, int):
                    curr = curr[key]

    def _merge_sequence_unique(self, data: Any, path: list[str | int], value: list[Any]) -> None:
        curr = data
        for i, key in enumerate(path):
            if i == len(path) - 1:
                if isinstance(curr, dict):
                    if key not in curr:
                        curr[key] = []
                    target = curr[key]
                elif isinstance(curr, list) and isinstance(key, int):
                    target = curr[key]
                else:
                    return

                if not isinstance(target, list):
                    return

                existing = set(target)
                for item in value:
                    if item not in existing:
                        target.append(item)
            else:
                if isinstance(curr, dict):
                    if key not in curr:
                        curr[key] = {}
                    curr = curr[key]
                elif isinstance(curr, list) and isinstance(key, int):
                    curr = curr[key]
