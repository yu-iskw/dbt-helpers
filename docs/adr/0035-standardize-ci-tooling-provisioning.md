# 35. Standardize CI Tooling Provisioning

Date: 2026-02-17

## Status

Accepted

## Context

The GitHub Action workflows in the `dbt-helpers` repository are failing during the "Install dependencies" step. The `dev/setup.sh` script requires `uv` and `trunk` to be installed on the host runner, but these tools are not pre-installed on the default GitHub Action runners (`ubuntu-latest`).

The current error is:

```shell
Error: Missing required tools: uv trunk
Please install these tools before running setup.
```

To ensure reliable and reproducible CI/CD runs, we need a standardized way to provision these essential tools across all workflows.

## Decision

We will standardize on using official GitHub Actions for provisioning `uv` and `trunk` at the beginning of each relevant job.

1. **Use \`astral-sh/setup-uv@v5\`**: This is the official action for installing the \`uv\` package manager. We will use it to ensure \`uv\` is available for dependency management and running scripts.
2. **Use \`trunk-io/trunk-action@v1\`**: This is the official action for installing and running the \`trunk\` CLI. While primarily used for linting, it also manages various other tools hermetically.
3. **Sequence**: These setup steps will be placed before any scripts that rely on these tools (e.g., \`bash dev/setup.sh\`).

## Consequences

### Positive

- **Reliability**: Workflows will no longer fail due to missing environment prerequisites.
- **Maintainability**: Using official actions ensures we get the latest stable versions and optimizations (like caching) provided by the tool authors.
- **Consistency**: All developers and CI runners will use the same tool versions.
- **Simplified Setup**: The \`dev/setup.sh\` script remains lean and doesn't need to handle complex tool installations itself.

### Negative

- **Workflow Runtime**: Adding setup steps adds a few seconds to each workflow run (mitigated by caching).
- **External Dependencies**: Our CI now depends on these third-party actions being available and working.
