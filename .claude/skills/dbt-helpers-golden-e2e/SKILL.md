---
name: dbt-helpers-golden-e2e
description: Implement and run End-to-End tests using golden output comparison. Use when verifying CLI behavior, plan generation, or full project execution.
---

# dbt-helpers-golden-e2e

## Purpose

To ensure that the CLI and core orchestrator produce the expected results for a given project state. Golden tests provide a high-level safety net for the entire system.

## Workflow

1. **Setup**: Use sample dbt projects in `integration_tests/`.
2. **Execute**: Run the `dbth` CLI command with a specific configuration.
3. **Compare**: Compare the generated plan (JSON/Text) or the final file state against "Golden" files stored in version control.

## Instructions

### When writing an E2E test

1. Identify or create a sample dbt project in `integration_tests/`.
2. Run the command and capture the output (e.g., `dbth source generate --plan`).
3. If this is a new test, save the output as the initial golden file.
4. If this is an existing test, verify that the output matches the golden file.

### When updating behavior

1. If the change is intentional, update the golden files (e.g., `pytest --update-goldens`).
2. Verify the diff to ensure no unexpected changes occurred.

## References

- [System Design: Levels of Testing](../../../docs/core/system_design.md#3-levels-of-testing)
- [Example sample projects in `integration_tests/`](../../../integration_tests/)
