import nox

# Define the dbt version and flavor matrix
# (flavor, version)
DBT_TEST_MATRIX = [
    ("core", "1.10"),
    ("core", "1.11"),
    ("fusion", "latest"),
]
CI_PYTHON_VERSIONS = ["3.10", "3.11", "3.12"]

nox.options.default_venv_backend = "uv"
nox.options.download_python = "auto"
nox.options.reuse_venv = "yes"


@nox.session(name="ci_tests", python=CI_PYTHON_VERSIONS, tags=["ci"])
def ci_tests(session):
    """Run CI tests in an isolated uv-backed environment."""
    env = {"UV_PROJECT_ENVIRONMENT": str(session.virtualenv.location)}
    session.run_install(
        "uv",
        "sync",
        "--frozen",
        "--all-extras",
        f"--python={session.virtualenv.location}",
        env=env,
    )
    session.run("bash", "dev/test_python.sh", external=True, env=env)


@nox.session(python=["3.12"])
def lint(session):
    """Run linters."""
    session.run("make", "lint", external=True)


@nox.session(python=["3.12"])
def test(session):
    """Run all tests."""
    session.run("make", "test", external=True)


@nox.session(python=["3.12"])
@nox.parametrize("flavor,version", DBT_TEST_MATRIX)
def integration_duckdb(session, flavor, version):
    """Run DuckDB integration tests for a specific dbt version."""
    session.install("pytest", "testcontainers", "docker", "pyyaml")

    session.install("-e", "src/dbt_helpers_sdk")
    session.install("-e", "src/dbt_helpers_core")
    session.install("-e", "src/plugins/schemas/dbt_helpers_schema_dbt")
    session.install("-e", "src/plugins/warehouses/dbt_helpers_wh_duckdb")

    session.env["USE_DOCKER"] = "true"
    session.run(
        "pytest",
        "src/plugins/warehouses/dbt_helpers_wh_duckdb/tests/integration",
        "-k",
        f"{flavor}-{version}",
        *session.posargs,
    )
