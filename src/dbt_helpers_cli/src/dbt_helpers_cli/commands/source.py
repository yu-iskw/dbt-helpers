from pathlib import Path
from typing import Annotated

import typer

from dbt_helpers_core.orchestrator import Orchestrator

from ..utils import console, print_plan

app = typer.Typer(help="Manage dbt sources")


@app.command("import")
def source_import(
    scope: Annotated[
        list[str],
        typer.Option("--scope", "-s", help="Scope of catalog to read (e.g. schema name)"),
    ],
    project_dir: Annotated[Path | None, typer.Option("--project-dir", "-p", help="Path to dbt project")] = None,
    apply: Annotated[bool, typer.Option("--apply", help="Apply changes to the dbt project")] = False,
    out: Annotated[Path | None, typer.Option("--out", "-o", help="Save the plan to a JSON file")] = None,
):
    """Import dbt Sources from warehouse metadata."""
    actual_project_dir = project_dir or Path.cwd()
    orchestrator = Orchestrator(actual_project_dir)

    try:
        plan = orchestrator.generate_source_plan(scope)

        if out:
            plan.save(out)
            console.print(f"[green]Plan saved to {out}[/green]")

        print_plan(plan, actual_project_dir)

        if not plan.ops:
            console.print("[green]No changes detected.[/green]")
            return

        if apply:
            console.print(
                "\n[yellow]Warning: Inline application via --apply is deprecated. "
                "Please use --out plan.json followed by 'dbth apply plan.json' for safer execution.[/yellow]"
            )
            if typer.confirm("Do you want to apply these changes?"):
                orchestrator.apply_plan(plan)
                console.print("[bold green]Plan applied successfully![/bold green]")
                console.print(f"Audit log: {orchestrator.project_dir}/.dbt_helpers/audit.jsonl")
        else:
            console.print("\n[yellow]Run with --apply to execute this plan.[/yellow]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1) from e


@app.command("sync")
def source_sync(
    scope: Annotated[
        list[str],
        typer.Option("--scope", "-s", help="Scope of catalog to read (e.g. schema name)"),
    ],
    project_dir: Annotated[Path | None, typer.Option("--project-dir", "-p", help="Path to dbt project")] = None,
    apply: Annotated[bool, typer.Option("--apply", help="Apply changes to the dbt project")] = False,
    out: Annotated[Path | None, typer.Option("--out", "-o", help="Save the plan to a JSON file")] = None,
):
    """Sync existing dbt Sources with warehouse metadata."""
    actual_project_dir = project_dir or Path.cwd()
    orchestrator = Orchestrator(actual_project_dir)

    try:
        plan = orchestrator.sync_sources(scope)

        if out:
            plan.save(out)
            console.print(f"[green]Plan saved to {out}[/green]")

        print_plan(plan, actual_project_dir)

        if not plan.ops:
            console.print("[green]No changes detected.[/green]")
            return

        if apply:
            console.print(
                "\n[yellow]Warning: Inline application via --apply is deprecated. "
                "Please use --out plan.json followed by 'dbth apply plan.json' for safer execution.[/yellow]"
            )
            if typer.confirm("Do you want to apply these changes?"):
                orchestrator.apply_plan(plan)
                console.print("[bold green]Plan applied successfully![/bold green]")
                console.print(f"Audit log: {orchestrator.project_dir}/.dbt_helpers/audit.jsonl")
        else:
            console.print("\n[yellow]Run with --apply to execute this plan.[/yellow]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1) from e
