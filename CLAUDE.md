# Python Package Template - Claude Code Memory

## Project Overview

This is a production-ready Python package template using modern tooling:

- **Package Manager**: uv (fast Python package manager)
- **Build System**: Hatchling
- **Linting/Formatting**: Trunk (manages Ruff, Mypy, Black, isort, Pylint, Bandit)
- **Testing**: pytest
- **Python**: 3.10+ (see `.python-version` for current version)

## Prerequisites (macOS)

For the best experience on macOS, install the core tooling via Homebrew to avoid path and permission issues:

```bash
brew install --cask trunk-io
brew install uv
```

Note: The binaries are typically located in `/opt/homebrew/bin/`. Ensure this is in your `PATH`.

## Quick Commands

```bash
make setup      # Install dependencies and set up environment
make lint       # Run all linters via Trunk
make format     # Auto-format code via Trunk
make test       # Run pytest test suite
make build      # Build the package
make clean      # Clean build artifacts
```

## Code Style

- Follow Google Python Style Guide (configured in `.pylintrc`)
- Use type hints for all public functions
- Imports sorted by Ruff (configured in `pyproject.toml`)
- Max line length: 120 characters (Ruff/Black configured)
- Use `snake_case` for functions/variables, `PascalCase` for classes

## Testing

- **Standardization**: All unit and integration tests MUST use `unittest.TestCase` (ADR 0015, 0017).
- **Assertions**: Use `self.assert*` methods instead of bare `assert`.
- **Location**: Unit tests in `tests/unit/`, integration tests in `tests/integration/` of each package (ADR 0009).
- **Integration Strategy**:
  - **Scenario-Driven**: Use `Scenario` (code-based) or `DirectoryScenario` (disk-based) for warehouse testing (ADR 0031, 0032).
  - **Multi-Version**: Integration tests parameterized across dbt versions/flavors via `pytest` and Docker (ADR 0033).
- **Runners**:
  - `make test`: Runs `pytest` across the monorepo.
  - `nox`: Used for running the multi-version dbt matrix.

## Git Workflow

- Create feature branches from `main`
- Run `make lint && make test` before commits
- Commit messages: `type(scope): description` (e.g., `feat(api): add user endpoint`)
- Types: feat, fix, docs, style, refactor, test, chore
- Record changes for release using the `manage-changelog` skill when `changie` is available (add fragments, batch releases, merge into CHANGELOG.md)

## Architecture

- **Hexagonal Architecture**: Plugin-based design with a stable Core, SDK (Ports/IR), and Adapters (ADR 0002).
- **Monorepo Layout**:
  - `src/dbt_helpers_core/`: Domain logic, orchestrator, and workflows (ADR 0024).
  - `src/dbt_helpers_sdk/`: Stable contracts, IR types, and Plan API (ADR 0025).
  - `src/dbt_helpers_cli/`: Modular CLI command structure (ADR 0014).
  - `src/plugins/`: Categorized adapters (ADR 0007).
    - `warehouses/`: DuckDB, BigQuery, Snowflake.
    - `tools/`: Lightdash, Elementary.
    - `schemas/`: dbt Core version adapters.
- **Workflow**: Two-phase "Plan and Apply" (ADR 0034).
  - Phase 1: Planning (`model scaffold`, `source sync`) generates a serialized JSON plan.
  - Phase 2: Application (`dbth apply`) executes the plan after review.
- **Resource Management**: IR-centric management; dbt 1.10+ only (ADR 0025).
- **Naming**: Warehouse-driven resource naming (ADR 0030).
- **Config**: Standardized SQL/YAML configuration blocks (ADR 0026, 0027).
- **Decision Records**: Significant design decisions recorded in `docs/adr/`.

## Significant ADRs

- **ADR 0002**: Hexagonal Architecture & Plugin SDK.
- **ADR 0015/0017**: Standardize on `unittest.TestCase` for all tests.
- **ADR 0025**: IR-Centric Resource Management & dbt 1.10+ requirement.
- **ADR 0031/0032**: Scenario-Driven Integration Testing.
- **ADR 0033**: Multi-Version dbt & Fusion Integration Testing.
- **ADR 0034**: Separate Plan and Apply Phases.

## Common Gotchas

- Always use `uv run` to execute commands in the virtual environment
- Trunk manages tool versions hermetically - don't install linters globally
- The `uv.lock` file is committed for reproducibility - don't gitignore it
- Run `trunk install` if linters report missing tools

## Parallel Task Execution

For large tasks that can benefit from concurrent work:

```bash
/parallel-executor Add comprehensive logging to all modules
```

This decomposes tasks into independent subtasks with file ownership, executes them in parallel, and verifies results.

## Available Agents

| Agent               | Purpose                                                         |
| :------------------ | :-------------------------------------------------------------- |
| `verifier`          | Run build → lint → test cycle across monorepo                   |
| `code-reviewer`     | Review code for quality, security, and ADR compliance           |
| `plugin-engineer`   | Specialist for building/testing plugins (Warehouse/Tool/Schema) |
| `schema-specialist` | Specialist for dbt YAML version adapters and IR mapping         |
| `sdk-architect`     | Specialist for SDK contracts and IR types                       |
| `parallel-executor` | Orchestrate parallel task execution                             |

See [AGENTS.md](AGENTS.md) for the full catalog of specialized agents.

## Available Skills

Use these when the corresponding CLI is available (`adr`, `changie`):

| Skill                         | Purpose                                             |
| :---------------------------- | :-------------------------------------------------- |
| `dbt-helpers-plugin-scaffold` | Scaffold and standardize new dbt-helpers plugins    |
| `dbt-helpers-golden-e2e`      | Run End-to-End tests using golden output comparison |
| `manage-adr`                  | Manage Architecture Decision Records in `docs/adr`  |
| `manage-changelog`            | Manage changelogs with Changie                      |

See [AGENTS.md](AGENTS.md) for the full catalog of specialized skills.

## Self-Improvement

This project supports Claude Code self-improvement. When you notice:

- Repeated mistakes Claude makes, add rules to this file
- New workflows you explain often, create skills in `.claude/skills/`
- Patterns that should be automated, add hooks in `.claude/settings.json`

Use `/improve-claude-config` skill to help Claude evolve its own configuration.

## Documentation Synchronization

- **ADR-Doc Sync**: After creating or modifying an ADR, ALWAYS perform a sync pass to update `CLAUDE.md` and `AGENTS.md` to reflect the new architectural state.
- **Skill-Doc Sync**: After creating or modifying a skill, ensure it is documented in `AGENTS.md`.
