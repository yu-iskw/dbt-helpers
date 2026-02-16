from rich.console import Console
from rich.table import Table

console = Console()


def print_plan(plan):
    console.print("[bold blue]Proposed Plan:[/bold blue]")
    table = Table("Op", "Path", "Details")
    for op in plan.ops:
        # Safely get patch_ops or other details
        details = ""
        if hasattr(op, "patch_ops"):
            details = str(op.patch_ops)
        elif hasattr(op, "content"):
            details = op.content[:50].replace("\n", " ") + "..."

        table.add_row(op.op_kind, str(op.path), details)
    console.print(table)
