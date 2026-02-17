from typing import Any

from dbt_helpers_sdk import DbtResourceIR, PatchOp


def calculate_resource_patch(current_ir: DbtResourceIR, new_ir: DbtResourceIR, base_path: list[Any]) -> list[PatchOp]:
    """Calculate patches to transform current_ir to new_ir at the given base_path."""
    patches = []

    # 1. Compare table-level fields
    # Only sync if current is empty but new has a value (don't overwrite manual edits)
    if not current_ir.description and new_ir.description:
        patches.append(PatchOp(op="upsert_mapping_key", path=[*base_path, "description"], value=new_ir.description))

    # For meta and tags, we might want to merge or just upsert.
    # Policy: merge warehouse meta/tags into dbt.
    if new_ir.meta:
        # We need a 'merge_mapping' op or similar. For now let's assume 'upsert_mapping_key' on individual keys
        for k, v in new_ir.meta.items():
            if k == "_extraction_metadata":
                continue
            if k not in current_ir.meta:
                patches.append(PatchOp(op="upsert_mapping_key", path=[*base_path, "meta", k], value=v))

    if new_ir.tags:
        for tag in new_ir.tags:
            if tag not in current_ir.tags:
                patches.append(PatchOp(op="merge_sequence_unique", path=[*base_path, "tags"], value=[tag]))

    # 2. Compare columns
    current_cols = {col.name: col for col in current_ir.columns}
    new_cols = {col.name: col for col in new_ir.columns}

    # Added columns
    for col_name, new_col in new_cols.items():
        if col_name not in current_cols:
            # We use a special 'upsert_list_item' or similar if we want to be smart.
            # For now, let's assume 'merge_sequence_unique' can handle dicts if we are careful,
            # or we define a more specific op.

            # Let's use a new op kind: 'upsert_item_in_list'
            # value is the whole column dict
            col_data = {
                "name": new_col.name,
            }
            if new_col.description:
                col_data["description"] = new_col.description
            if new_col.data_type:
                col_data["data_type"] = new_col.data_type # dbt Core 1.10+ uses data_type

            patches.append(PatchOp(
                op="merge_sequence_unique",
                path=[*base_path, "columns"],
                value=[col_data]
            ))
        else:
            # Existing column - compare fields
            curr_col = current_cols[col_name]
            col_path = [*base_path, "columns", {"name": col_name}]

            # Update data_type if changed
            if new_col.data_type and curr_col.data_type != new_col.data_type:
                patches.append(PatchOp(
                    op="upsert_mapping_key",
                    path=[*col_path, "data_type"],
                    value=new_col.data_type
                ))

            # Update description ONLY if it was empty in current but exists in new?
            # Or always update? Usually we don't want to overwrite manual descriptions.
            # Policy: If current is empty/None, and new has it, sync it.
            if not curr_col.description and new_col.description:
                patches.append(PatchOp(
                    op="upsert_mapping_key",
                    path=[*col_path, "description"],
                    value=new_col.description
                ))

    return patches
