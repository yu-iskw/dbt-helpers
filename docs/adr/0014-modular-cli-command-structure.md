# 14. Modular CLI Command Structure

Date: 2026-02-16

## Status

Accepted

## Context

As the `dbt-helpers` CLI grows, the `main.py` file in `dbt_helpers_cli` is becoming a monolithic module containing logic for all subcommands (sources, models, etc.). This makes the codebase harder to maintain, test, and extend. We need a more modular structure to organize CLI commands.

## Decision

We will restructure the `dbt-helpers-cli` package to separate command groups into dedicated modules under a `commands/` subpackage.

1.  **Shared Utilities**: Move shared CLI logic (like plan printing) to `dbt_helpers_cli.utils`.
2.  **Command Modules**: Create `dbt_helpers_cli.commands` subpackage.
    - `commands/source.py`: Logic for the `dbth source` group.
    - `commands/model.py`: Logic for the `dbth model` group.
3.  **Main Registry**: `main.py` will serve as the entry point, responsible only for initializing the `typer.Typer` app and registering subcommand groups from the command modules.

## Consequences

- **Improved Maintainability**: Smaller, focused files are easier to navigate and understand.
- **Parallel Development**: Different developers can work on separate command modules with fewer merge conflicts.
- **Scalability**: Adding new command groups (e.g., `dbth test`, `dbth docs`) simply involves creating a new module in `commands/`.
- **Encapsulation**: Command-specific logic is isolated from the main entry point and other command groups.
