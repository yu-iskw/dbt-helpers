from pathlib import Path
from typing import Annotated

import typer

from dbt_helpers_core.orchestrator import Orchestrator

from ..utils import console, print_plan

app = typer.Typer(help="Manage dbt models")


@app.command("scaffold")
def model_scaffold(
    scope: Annotated[
        list[str],
        typer.Option("--scope", "-s", help="Scope of catalog to read (e.g. schema name)"),
    ],
    project_dir: Annotated[
        Path | None, typer.Option("--project-dir", "-p", help="Path to dbt project")
    ] = None,
    plan_only: Annotated[bool, typer.Option("--plan", help="Only show plan")] = True,
):
    """Generate dbt Model scaffolds based on warehouse tables."""
    actual_project_dir = project_dir or Path.cwd()
    orchestrator = Orchestrator(actual_project_dir)

    try:
        plan = orchestrator.scaffold_models(scope)

        if plan_only:
            print_plan(plan)
        else:
            console.print(
                "[yellow]Apply functionality is not yet implemented in this MVP.[/yellow]"
            )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1) from e
