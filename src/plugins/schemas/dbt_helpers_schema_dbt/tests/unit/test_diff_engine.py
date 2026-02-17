import unittest

from dbt_helpers_schema_dbt.diff_engine import calculate_resource_patch
from dbt_helpers_sdk import DbtColumnIR, DbtResourceIR


class TestDiffEngine(unittest.TestCase):
    """Tests for the dbt schema diff engine."""
    def test_calculate_resource_patch_added_column(self):
        current_ir = DbtResourceIR(
            name="my_table",
            columns=[DbtColumnIR(name="id", data_type="integer")]
        )
        new_ir = DbtResourceIR(
            name="my_table",
            columns=[
                DbtColumnIR(name="id", data_type="integer"),
                DbtColumnIR(name="email", data_type="string")
            ]
        )
        base_path = ["sources", {"name": "raw"}, "tables", {"name": "my_table"}]

        patches = calculate_resource_patch(current_ir, new_ir, base_path)

        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0].op, "merge_sequence_unique")
        self.assertEqual(patches[0].path, [*base_path, "columns"])
        self.assertEqual(patches[0].value[0]["name"], "email")

    def test_calculate_resource_patch_updated_column(self):
        current_ir = DbtResourceIR(
            name="my_table",
            columns=[DbtColumnIR(name="id", data_type="integer")]
        )
        new_ir = DbtResourceIR(
            name="my_table",
            columns=[DbtColumnIR(name="id", data_type="string", description="the id")]
        )
        base_path = ["sources", {"name": "raw"}, "tables", {"name": "my_table"}]

        patches = calculate_resource_patch(current_ir, new_ir, base_path)

        # 1. data_type change, 2. description added
        self.assertEqual(len(patches), 2)

        data_type_patch = next(p for p in patches if p.path[-1] == "data_type")
        self.assertEqual(data_type_patch.value, "string")

        desc_patch = next(p for p in patches if p.path[-1] == "description")
        self.assertEqual(desc_patch.value, "the id")

if __name__ == "__main__":
    unittest.main()
