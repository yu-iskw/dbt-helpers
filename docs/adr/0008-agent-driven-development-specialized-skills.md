# 8. Agent-Driven Development with Specialized Skills

Date: 2026-02-16

## Status

Accepted

## Context

The `dbt-helpers` project follows a complex architectural pattern including Hexagonal Architecture, Nullable Infrastructure for testing, and a Plan API for safe file operations. Developing these components manually or with general-purpose AI agents can lead to inconsistencies, architectural drift, and slower development cycles. We need a way to encode our architectural decisions and specialized workflows into the AI tools we use for development.

## Decision

We will adopt an "Agent-Driven Development" approach by implementing specialized agent skills and subagents before the core implementation of `dbt-helpers`.

1. **Specialized Skills**: We will create 7 focused skills in `.claude/skills/` that encode domain-specific knowledge:

   - `dbt-helpers-sdk-contract`: Focuses on IR types and Plan API stability.
   - `dbt-helpers-nullable-testing`: Implements the Nullable Infrastructure pattern.
   - `dbt-helpers-plugin-scaffold`: Standardizes plugin creation.
   - `dbt-helpers-integration-testcontainers`: Manages container-based integration tests.
   - `dbt-helpers-schema-adapter`: Handles dbt YAML version mapping.
   - `dbt-helpers-golden-e2e`: Automates CLI verification.
   - `dbt-helpers-path-policy`: Enforces path templating rules.

2. **Specialized Subagents**: We will create 5 specialized subagents in `.claude/agents/` that leverage these skills to perform specific roles (e.g., `sdk-architect`, `plugin-engineer`).

3. **Skills-First Workflow**: New features and components will be developed using these specialized agents to ensure compliance with the system design.

## Consequences

- **Architectural Alignment**: The AI agents will "know" the system design and enforce it during implementation.
- **Consistency**: All plugins and core components will follow the same patterns for testing and I/O.
- **Automation**: Repetitive tasks like plugin scaffolding and test setup will be automated.
- **Quality**: TDD cycles will be reinforced by specialized verification agents.
- **Maintenance**: Skills and agents will need to be updated as the system design evolves.
