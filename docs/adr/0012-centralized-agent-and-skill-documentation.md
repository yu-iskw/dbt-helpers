# 12. Centralized Agent and Skill Documentation

Date: 2026-02-16

## Status

Accepted

## Context

As the number of specialized agents (e.g., `plugin-engineer`, `schema-specialist`) and skills (e.g., `dbt-helpers-*`) grows, the `CLAUDE.md` file is becoming cluttered and difficult to navigate. At the same time, these tools are critical for the correct development and maintenance of the `dbt-helpers` project. Without clear documentation, agents may not realize these specialized capabilities exist, leading to sub-optimal task execution or duplication of effort.

## Decision

We will adopt a "Curated High-Impact" documentation strategy:

1. **Centralized Catalog**: Create a new `AGENTS.md` file in the project root to serve as a comprehensive, categorized catalog of all available agents and skills.
2. **Curated Primary Context**: Update `CLAUDE.md` to list only the most significant and frequently used tools, serving as a high-level entry point.
3. **Cross-Referencing**: Include a clear reference in `CLAUDE.md` pointing to `AGENTS.md` for the full list of capabilities.

## Consequences

- **Improved Discoverability**: Specialized domain tools are explicitly documented, making it easier for AI agents to find and use the right tool for the job.
- **Reduced Clutter**: `CLAUDE.md` remains focused on core project rules and high-impact commands.
- **Better Specialized Workflows**: By categorizing tools in `AGENTS.md`, we provide clearer guidance on which tools to use for specific phases of development (e.g., "Core Engineering", "Quality Assurance").
- **Maintenance Overhead**: Developers must now remember to update `AGENTS.md` when adding new agents or skills, though this is mitigated by the clearer structure.
