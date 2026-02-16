# 9. Monorepo Test and Makefile Organization

Date: 2026-02-16

## Status

Accepted

## Context

As the `dbt-helpers` project transitions to a monorepo structure with multiple packages (SDK, Core, CLI, and various plugins), we need a standardized way to manage tasks and tests within each package while maintaining centralized orchestration.

## Decision

We will implement a hierarchical Makefile and test structure:

1.  **Package-level Makefiles**: Every package in `src/` or `src/plugins/` will have its own `Makefile` implementing standard targets like `test`.
2.  **Package-level Tests**: Unit tests will be co-located with each package in a `tests/unit/` directory.
3.  **Root Makefile Orchestration**: The root `Makefile` will delegate tasks to sub-package Makefiles. For example, `make test` at the root will run `make test` in all sub-packages.
4.  **Tooling**: Use `uv run pytest` for running tests to ensure the correct environment and dependencies are used for each package.

## Consequences

- **Isolation**: Packages can be tested and operated independently.
- **Consistency**: All packages follow the same interface for common development tasks.
- **Centralized Control**: The root Makefile remains the entry point for CI/CD and overall project management.
- **Maintenance**: Requires adding and maintaining Makefiles and test directories for every new package added to the monorepo.
