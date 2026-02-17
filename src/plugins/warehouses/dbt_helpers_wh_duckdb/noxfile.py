import nox

# Use the same matrix as conftest.py or allow overriding
DBT_CORE_VERSIONS = ["1.10", "1.11"]

@nox.session(python=["3.12"])
def integration(session):
    """Run integration tests across the dbt version matrix using Docker."""
    # Install dependencies
    # Using uv for faster installation if available, otherwise pip
    session.install("pytest", "pytest-cov", "testcontainers", "docker", "pyyaml")

    # Install internal packages
    session.install("../../../dbt_helpers_sdk")
    session.install("../../../dbt_helpers_core")
    session.install(".")

    # Run integration tests with Docker enabled
    # The matrix is handled by pytest parameterization in conftest.py
    session.env["USE_DOCKER"] = "true"
    session.run("pytest", "tests/integration", *session.posargs)

@nox.session(python=["3.12"])
@nox.parametrize("version", DBT_CORE_VERSIONS)
def integration_core(session, version):
    """Run integration tests for a specific dbt Core version."""
    session.install("pytest", "pytest-cov", "testcontainers", "docker", "pyyaml")
    session.install("../../../dbt_helpers_sdk")
    session.install("../../../dbt_helpers_core")
    session.install(".")

    session.env["USE_DOCKER"] = "true"
    # We can pass flags to pytest if we want to filter,
    # but for now we rely on the full matrix run.
    # To run a specific version, we might need to update conftest.py
    # to accept command line arguments.
    session.run("pytest", "tests/integration", "-k", f"core-{version}", *session.posargs)

@nox.session(python=["3.12"])
def integration_fusion(session):
    """Run integration tests for dbt Fusion (expected to be skipped currently)."""
    session.install("pytest", "pytest-cov", "testcontainers", "docker", "pyyaml")
    session.install("../../../dbt_helpers_sdk")
    session.install("../../../dbt_helpers_core")
    session.install(".")

    session.env["USE_DOCKER"] = "true"
    session.run("pytest", "tests/integration", "-k", "fusion-latest", *session.posargs)
