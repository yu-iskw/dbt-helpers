# Agents and Skills Catalog

This document provides a comprehensive list of specialized AI agents and skills available in the `dbt-helpers` repository. These tools are designed to work together to ensure high-quality, architecturally sound, and well-tested implementations.

## Navigation

- [Core Engineering Agents](#core-engineering-agents)
- [Quality and Verification Agents](#quality-and-verification-agents)
- [Task Orchestration Agents](#task-orchestration-agents)
- [Domain-Specific Skills (dbt-helpers)](#domain-specific-skills-dbt-helpers)
- [General Workflow Skills](#general-workflow-skills)

---

## Core Engineering Agents

These agents are specialists in the primary architectural layers of the project.

| Agent               | Purpose                                                                           | Significant Skills                                                      |
| :------------------ | :-------------------------------------------------------------------------------- | :---------------------------------------------------------------------- |
| `plugin-engineer`   | Specialist for building and testing `dbt-helpers` plugins (Warehouses and Tools). | `dbt-helpers-plugin-scaffold`, `dbt-helpers-integration-testcontainers` |
| `schema-specialist` | Specialist for dbt YAML version adapters and migrations.                          | `dbt-helpers-schema-adapter`                                            |
| `path-architect`    | Specialist for path templating, naming policies, and resource organization.       | `dbt-helpers-path-policy`                                               |
| `sdk-architect`     | Specialist for SDK design, IR types, and stable contracts.                        | `dbt-helpers-sdk-contract`, `dbt-helpers-nullable-testing`              |

---

## Quality and Verification Agents

These agents ensure that implementations meet the project's high standards for quality and security.

| Agent              | Purpose                                                                                      | Significant Skills                                       |
| :----------------- | :------------------------------------------------------------------------------------------- | :------------------------------------------------------- |
| `verifier`         | Runs the full build → lint → test cycle to ensure repository health.                         | `lint-and-fix`, `test-and-fix`                           |
| `code-reviewer`    | Expert reviewer focused on code quality, security, and best practices.                       | N/A                                                      |
| `quality-verifier` | Comprehensive verification specialist. Focuses on golden tests and architectural compliance. | `dbt-helpers-golden-e2e`, `dbt-helpers-nullable-testing` |

---

## Task Orchestration Agents

These agents handle complex, large-scale tasks by decomposing them into manageable subtasks.

| Agent                    | Purpose                                                                                  | Significant Skills  |
| :----------------------- | :--------------------------------------------------------------------------------------- | :------------------ |
| `parallel-executor`      | Orchestrates parallel task execution across the repository.                              | `parallel-executor` |
| `parallel-tasks-planner` | Decomposes complex requirements into discrete, mutually exclusive subtasks.              | N/A                 |
| `task-worker`            | Generic worker agent for executing isolated subtasks under the direction of an executor. | N/A                 |

---

## Domain-Specific Skills (dbt-helpers)

Specialized skills for working within the `dbt-helpers` ecosystem.

| Skill                                    | Description                                                                          |
| :--------------------------------------- | :----------------------------------------------------------------------------------- |
| `dbt-helpers-plugin-scaffold`            | Scaffold and standardize new plugins (Warehouse, Tool, or Schema).                   |
| `dbt-helpers-sdk-contract`               | Manage and enforce SDK contracts, IR types, and the Plan API.                        |
| `dbt-helpers-golden-e2e`                 | Implement and run End-to-End tests using golden output comparison.                   |
| `dbt-helpers-nullable-testing`           | Implement and use Nullable Infrastructure adapters for mock-free testing.            |
| `dbt-helpers-integration-testcontainers` | Set up and run integration tests against real database engines using Testcontainers. |
| `dbt-helpers-path-policy`                | Manage and enforce path templating and naming conventions.                           |
| `dbt-helpers-schema-adapter`             | Implement and manage dbt YAML schema adapters for bi-directional mapping.            |

---

## General Workflow Skills

General-purpose skills for project maintenance and common development tasks.

| Skill                          | Description                                                            |
| :----------------------------- | :--------------------------------------------------------------------- |
| `pr-workflow`                  | Complete pull request workflow from branch creation to submission.     |
| `fix-issue`                    | End-to-end workflow for fixing GitHub issues.                          |
| `setup-dev-env`                | Set up the development environment, including dependencies and tools.  |
| `lint-and-fix`                 | Run linters and automatically fix style or formatting violations.      |
| `test-and-fix`                 | Run unit tests and automatically fix failures.                         |
| `python-upgrade`               | Safely upgrade Python dependencies using `uv`.                         |
| `manage-adr`                   | Create and manage Architecture Decision Records in `docs/adr`.         |
| `manage-changelog`             | Manage changelogs and release fragments using Changie.                 |
| `improve-claude-config`        | Self-improvement skill for evolving Claude Code configuration.         |
| `initialize-project`           | Initialize a new project from the Python package template.             |
| `security-vulnerability-audit` | Audit and repair security vulnerabilities using Trivy and OSV-scanner. |

---

> [!TIP]
> To use a subagent, call it with the `/task` command (e.g., `/task plugin-engineer "implement bigquery catalog client"`). To use a skill, ensure the corresponding tool is available and refer to its documentation in `.claude/skills/`.
