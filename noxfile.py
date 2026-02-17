import nox

# Define the dbt version and flavor matrix
# (flavor, version)
DBT_TEST_MATRIX = [
    ("core", "1.10"),
    ("core", "1.11"),
    ("fusion", "latest"),
]

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
    
    # Install local workspace packages
    session.install("-e", "src/dbt_helpers_sdk")
    session.install("-e", "src/dbt_helpers_core")
    session.install("-e", "src/plugins/schemas/dbt_helpers_schema_dbt")
    session.install("-e", "src/plugins/warehouses/dbt_helpers_wh_duckdb")
    
    session.env["USE_DOCKER"] = "true"
    # Use -k to filter for the specific flavor-version in pytest
    session.run(
        "pytest", 
        "src/plugins/warehouses/dbt_helpers_wh_duckdb/tests/integration",
        "-k", f"{flavor}-{version}",
        *session.posargs
    )
