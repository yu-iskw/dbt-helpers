import difflib
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from dbt_helpers_core.yaml_store import YamlStore
from dbt_helpers_sdk import AddDiagnostics, CreateFile, DeleteFile, UpdateYamlFile

console = Console()


def print_deprecation_warning():
    """Print a prominent deprecation warning for inline application."""
    console.print(
        Panel(
            "[bold yellow]DEPRECATION WARNING:[/bold yellow]\n\n"
            "Inline application via [bold]--apply[/bold] is deprecated and will be removed in a future version.\n"
            "Please use the two-phase workflow:\n"
            "  1. [bold]dbth <command> --out plan.json[/bold]\n"
            "  2. [bold]dbth apply plan.json[/bold]\n\n"
            "This ensures safety and allows for auditing changes before execution.",
            border_style="yellow",
        )
    )
def print_plan(plan, project_dir: Path | None = None):
    """Print the plan in a rich, human-readable format."""
    if not plan.ops:
        console.print("[green]No changes detected.[/green]")
        return

    # Count operations
    add_count = sum(1 for op in plan.ops if isinstance(op, CreateFile))
    change_count = sum(1 for op in plan.ops if isinstance(op, UpdateYamlFile))
    delete_count = sum(1 for op in plan.ops if isinstance(op, DeleteFile))
    diag_count = sum(1 for op in plan.ops if isinstance(op, AddDiagnostics))

    console.print("\n[bold blue]Proposed Plan Summary:[/bold blue]")
    summary_text = Text()
    if add_count:
        summary_text.append(f" {add_count} to add", style="green")
    if change_count:
        summary_text.append(f" {change_count} to change", style="yellow")
    if delete_count:
        summary_text.append(f" {delete_count} to delete", style="red")
    if diag_count:
        summary_text.append(f" {diag_count} diagnostics", style="cyan")

    if summary_text:
        console.print(Panel(summary_text))

    table = Table("Op", "Path", "Summary", box=None)

    for op in plan.ops:
        summary = ""
        if isinstance(op, CreateFile):
            summary = f"Create new file with {len(op.content.splitlines())} lines"
        elif isinstance(op, UpdateYamlFile):
            summary = f"Apply {len(op.patch_ops)} YAML patches"
        elif isinstance(op, DeleteFile):
            summary = "Delete file"
        elif isinstance(op, AddDiagnostics):
            summary = op.message

        table.add_row(
            op.op_kind.upper().replace("_", " "),
            str(getattr(op, "path", "")),
            summary,
        )

    console.print(table)
    console.print("-" * 40)

    yaml_store = YamlStore()

    for op in plan.ops:
        path_str = f": {op.path}" if hasattr(op, "path") else ""
        console.print(f"\n[bold]{op.op_kind.upper().replace('_', ' ')}{path_str}[/bold]")

        if isinstance(op, CreateFile):
            lexer = "sql" if op.path.suffix == ".sql" else "yaml" if op.path.suffix in (".yml", ".yaml") else "text"
            syntax = Syntax(op.content, lexer, theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title=f"New Content: {op.path}"))

        elif isinstance(op, UpdateYamlFile):
            if project_dir:
                full_path = project_dir / op.path
                if full_path.exists():
                    try:
                        old_content = full_path.read_text(encoding="utf-8")
                        new_content = yaml_store.patch(old_content, op.patch_ops)

                        diff = difflib.unified_diff(
                            old_content.splitlines(),
                            new_content.splitlines(),
                            fromfile=f"a/{op.path}",
                            tofile=f"b/{op.path}",
                            lineterm="",
                        )

                        diff_text = Text()
                        for line in diff:
                            if line.startswith("+") and not line.startswith("+++"):
                                diff_text.append(line + "\n", style="green")
                            elif line.startswith("-") and not line.startswith("---"):
                                diff_text.append(line + "\n", style="red")
                            elif line.startswith("@@"):
                                diff_text.append(line + "\n", style="cyan")
                            else:
                                diff_text.append(line + "\n")

                        if diff_text:
                            console.print(Panel(diff_text, title=f"Diff: {op.path}"))
                        else:
                            console.print("[yellow]No changes after patching (idempotent).[/yellow]")
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        console.print(f"[red]Error generating diff: {e}[/red]")
                else:
                    console.print(f"[yellow]File {op.path} does not exist. Cannot show diff.[/yellow]")
            else:
                # Fallback if project_dir is not provided
                for i, patch in enumerate(op.patch_ops):
                    console.print(f"  {i+1}. {patch.op} at {patch.path}")
                    if patch.value:
                        console.print(f"     Value: {patch.value}")

        elif isinstance(op, DeleteFile):
            console.print(f"[red]File will be deleted: {op.path}[/red]")

        elif isinstance(op, AddDiagnostics):
            style = "yellow" if op.level == "warning" else "red" if op.level == "error" else "white"
            console.print(f"[{style}]{op.level.upper()}: {op.message}[/{style}]")

    # Add Summary Table at the end
    counts: dict[str, int] = {}
    for op in plan.ops:
        counts[op.op_kind] = counts.get(op.op_kind, 0) + 1

    summary_table = Table(title="Plan Summary", box=None)
    summary_table.add_column("Operation", style="cyan")
    summary_table.add_column("Count", justify="right")

    for kind, count in sorted(counts.items()):
        summary_table.add_row(kind.upper().replace("_", " "), str(count))

    console.print("\n")
    console.print(summary_table)
