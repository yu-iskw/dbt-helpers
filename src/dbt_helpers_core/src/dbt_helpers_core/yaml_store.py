from io import StringIO
from typing import Any

from ruamel.yaml import YAML

from dbt_helpers_sdk import PatchOp


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

    def patch(self, content: str, patch_ops: list[PatchOp]) -> str:
        """Apply a series of patch operations to YAML content."""
        data = self.load(content)

        for patch_op in patch_ops:
            op = patch_op.op
            path = patch_op.path
            value = patch_op.value

            if op == "upsert_mapping_key":
                self._upsert_mapping_key(data, path, value)
            elif op == "merge_sequence_unique":
                if isinstance(value, list):
                    self._merge_sequence_unique(data, path, value)
            elif op == "delete_key":
                self._delete_key(data, path)
            elif op == "replace_content":
                data = self.load(str(value))

        return self.dump(data)

    def _navigate(self, data: Any, path: list[str | int | dict[str, Any]], create: bool = False) -> Any:
        curr = data
        for part in path:
            if isinstance(part, str):
                if isinstance(curr, dict):
                    if part not in curr:
                        if create:
                            curr[part] = {}
                        else:
                            raise KeyError(f"Key {part} not found")
                    curr = curr[part]
                else:
                    raise TypeError(f"Expected dict at {part}, got {type(curr)}")
            elif isinstance(part, int):
                if isinstance(curr, list):
                    curr = curr[part]
                else:
                    raise TypeError(f"Expected list at index {part}, got {type(curr)}")
            elif isinstance(part, dict):
                # Selector: {"name": "val"}
                if not isinstance(curr, list):
                    raise TypeError(f"Expected list for selector {part}, got {type(curr)}")

                key, val = next(iter(part.items()))
                found = None
                for item in curr:
                    if isinstance(item, dict) and item.get(key) == val:
                        found = item
                        break

                if found is None:
                    if create:
                        new_item = {key: val}
                        curr.append(new_item)
                        found = new_item
                    else:
                        raise KeyError(f"Item with {key}={val} not found")
                curr = found
        return curr

    def _upsert_mapping_key(self, data: Any, path: list[str | int | dict[str, Any]], value: Any) -> None:
        if not path:
            return

        parent_path = path[:-1]
        last_key = path[-1]

        parent = self._navigate(data, parent_path, create=True)
        if isinstance(parent, dict) and isinstance(last_key, str):
            parent[last_key] = value
        else:
            raise TypeError(f"Cannot upsert key {last_key} in {type(parent)}")

    def _merge_sequence_unique(self, data: Any, path: list[str | int | dict[str, Any]], value: list[Any]) -> None:
        target = self._navigate(data, path, create=True)
        if not isinstance(target, list):
            raise TypeError(f"Expected list at {path}, got {type(target)}")

        # Unique by identity or by 'name' key if items are dicts
        for item in value:
            if isinstance(item, dict) and "name" in item:
                # Find by name
                found = False
                for existing in target:
                    if isinstance(existing, dict) and existing.get("name") == item["name"]:
                        found = True
                        # Potentially merge fields? For now just skip if exists.
                        break
                if not found:
                    target.append(item)
            elif item not in target:
                target.append(item)

    def _delete_key(self, data: Any, path: list[str | int | dict[str, Any]]) -> None:
        if not path:
            return
        parent_path = path[:-1]
        last_key = path[-1]

        try:
            parent = self._navigate(data, parent_path, create=False)
            if isinstance(parent, dict) and isinstance(last_key, str) and last_key in parent:
                del parent[last_key]
        except (KeyError, IndexError, TypeError):
            pass
