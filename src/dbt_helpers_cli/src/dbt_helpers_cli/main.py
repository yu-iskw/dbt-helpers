from pathlib import Path
from typing import Annotated

import typer

from dbt_helpers_core.orchestrator import Orchestrator
from dbt_helpers_sdk import Plan

from .commands.model import app as model_app
from .commands.snapshot import app as snapshot_app
from .commands.source import app as source_app
from .utils import console, print_plan

app = typer.Typer(help="dbt-helpers: A modular toolkit for dbt project management")

app.add_typer(source_app, name="source")
app.add_typer(model_app, name="model")
app.add_typer(snapshot_app, name="snapshot")


@app.command("apply")
def apply(
    plan_path: Annotated[Path, typer.Argument(help="Path to the plan JSON file")],
    project_dir: Annotated[Path | None, typer.Option("--project-dir", "-p", help="Path to dbt project")] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
):
    """Apply a saved plan to the dbt project."""
    actual_project_dir = project_dir or Path.cwd()

    try:
        if not plan_path.exists():
            console.print(f"[bold red]Error:[/bold red] Plan file {plan_path} not found.")
            raise typer.Exit(code=1)

        plan = Plan.load(plan_path)
        print_plan(plan, actual_project_dir)

        if not plan.ops:
            console.print("[green]Plan is empty. Nothing to apply.[/green]")
            return

        if yes or typer.confirm("Do you want to apply these changes?"):
            orchestrator = Orchestrator(actual_project_dir)
            orchestrator.apply_plan(plan)
            console.print("[bold green]Plan applied successfully![/bold green]")
            console.print(f"Audit log: {orchestrator.project_dir}/.dbt_helpers/audit.jsonl")
        else:
            console.print("[yellow]Application cancelled.[/yellow]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
