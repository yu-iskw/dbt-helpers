---
name: setup-dev-env
description: Set up the development environment for the project. Use when starting work on the project, when dependencies are out of sync, or to fix environment setup failures.
---

# Setup Development Environment

This skill automates the process of setting up the development environment to ensure all tools and dependencies are correctly installed and configured.

## Workflow Checklist

- [ ] **Step 1: Environment Validation**
  - [ ] Check Python version against `.python-version`
  - [ ] Check for `trunk` installation (including `/opt/homebrew/bin/trunk`)
  - [ ] Check for `uv` installation (including `/opt/homebrew/bin/uv`)
- [ ] **Step 2: macOS Prerequisites (if applicable)**
  - [ ] Install `trunk-io` and `uv` via Homebrew if missing
  - [ ] Ensure Homebrew bin is in `PATH`
- [ ] **Step 3: Dependency Installation**
  - [ ] Run `make setup`
- [ ] **Step 4: Tooling Setup**
  - [ ] Run `trunk install` to fetch managed linters and formatters

## Detailed Instructions

### 1. Environment Validation

#### Python Version

Read the `.python-version` file in the workspace root. Ensure the current Python environment matches this version. If there's a mismatch, inform the user to switch Python versions (e.g., using `pyenv` or `asdf`).

#### Tooling Installation (macOS Focus)

Check if `trunk` and `uv` are installed and available in the current `PATH`.
On macOS, prioritize Homebrew installation to avoid common pathing and permission issues.

**Check common locations:**

- `/opt/homebrew/bin/trunk`
- `/opt/homebrew/bin/uv`

If these tools are missing, install them via Homebrew:

```bash
brew install --cask trunk-io
brew install uv
```

**CRITICAL**: If the binaries exist in `/opt/homebrew/bin/` but are not in the current shell's `PATH`, advise the user to add it:

```bash
export PATH="/opt/homebrew/bin:$PATH"
```

### 2. Dependency Installation

Run the following command at the workspace root to install all project dependencies.

```bash
make setup
```

This command runs `dev/setup.sh`, which performs informative checks for `uv` and `trunk`, creates a virtual environment, and syncs dependencies.

### 3. Tooling Setup

Trunk manages linters and formatters hermetically. Run the following command to ensure all required tools are downloaded and ready.

```bash
trunk install
```

## Success Criteria

- All Python dependencies are installed successfully in the virtual environment.
- `trunk` and `uv` are installed.
- The Python version matches the requirement in `.python-version`.

## Post-Setup Verification

To ensure the environment is fully operational:

1. **Invoke Verifier**: Run the `verifier` subagent ([../../agents/verifier.md](../../agents/verifier.md)). This confirms that the freshly installed dependencies allow for a successful build, pass lint checks, and satisfy all unit tests.
2. **Handle Failure**: If the `verifier` fails, follow its reporting to resolve environment-specific issues.
