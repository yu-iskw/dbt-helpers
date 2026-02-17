"""Pytest fixtures for DuckDB integration tests (local and Docker)."""

import contextlib
import os
import shutil
import subprocess  # nosec B404
from pathlib import Path

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from .scenarios import Scenario, registry

# Define the dbt version and flavor matrix
# (flavor, version)
DBT_TEST_MATRIX = [
    ("core", "1.10"),
    ("core", "1.11"),
    ("fusion", "latest"),
]

@pytest.fixture(scope="session", params=DBT_TEST_MATRIX, ids=lambda x: f"{x[0]}-{x[1]}")
def dbt_config(request) -> tuple[str, str]:
    """Fixture for dbt flavor and version parameterization."""
    flavor, version = request.param
    if flavor == "fusion":
        pytest.skip(f"dbt Fusion does not yet support DuckDB adapter. Flavor: {flavor}, Version: {version}")
    return flavor, version

@pytest.fixture(scope="session", params=["sample_project"])
def scenario_name(request: pytest.FixtureRequest) -> str:
    """Fixture for scenario name parameterization."""
    return str(request.param)

def _docker_available() -> bool:
    """Check if Docker is available and running."""
    try:
        import docker  # pylint: disable=import-outside-toplevel

        client = docker.from_env()
        client.ping()
        return True
    except Exception:  # pylint: disable=broad-exception-caught
        return False

def _run_dbt_local(scenario: Scenario, db_path: Path, tmp_dir: Path) -> Path:
    """Run dbt build locally and return the database path."""
    scenario.write_to_disk(tmp_dir)

    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = str(tmp_dir)

    # Path in profiles.yml is relative to project root in write_to_disk
    # But we want to ensure it matches the requested db_path if possible
    # Actually, DuckDB in dbt-duckdb creates the file where specified.
    # Our write_to_disk creates a profiles.yml pointing to 'dev.duckdb'.

    subprocess.run(  # nosec B603, B607
        ["dbt", "build", "--project-dir", str(tmp_dir)],
        env=env,
        check=True,
        capture_output=True,
        cwd=str(tmp_dir),
    )

    generated_db = tmp_dir / "dev.duckdb"
    if generated_db.exists() and generated_db.resolve() != db_path.resolve():
        shutil.copy(generated_db, db_path)

    return db_path

def _run_dbt_docker(
    scenario: Scenario, db_path: Path, tmp_path_factory, flavor: str, version: str
) -> Path:
    """Run dbt build in Docker container and extract the database file."""
    integration_dir = Path(__file__).parent
    dockerfile_path = integration_dir / "Dockerfile"

    # Create a temporary directory for the dbt project
    project_dir = tmp_path_factory.mktemp("dbt_project")
    scenario.write_to_disk(project_dir)

    # Create a temporary directory for the database output
    output_dir = tmp_path_factory.mktemp("dbt_docker_output")
    container_db_path = output_dir / "dev.duckdb"

    # Build Docker image from Dockerfile
    container = (
        DockerContainer("python:3.12-slim")
        .with_kwargs(buildargs={"DBT_FLAVOR": flavor, "DBT_VERSION": version})
        .with_build_context(str(integration_dir))
        .with_dockerfile(str(dockerfile_path))
        .with_volume_mapping(str(project_dir), "/workspace")
        .with_volume_mapping(str(output_dir), "/output")
        .with_env("DBT_PROFILES_DIR", "/workspace")
    )

    # Override entrypoint to ensure output
    container = container.with_command(
        [
            "sh",
            "-c",
            "dbt build --project-dir /workspace && "
            "if [ -f /workspace/dev.duckdb ]; then cp /workspace/dev.duckdb /output/dev.duckdb; fi",
        ]
    )

    with container:
        # Wait for dbt build to complete
        with contextlib.suppress(Exception):  # pylint: disable=broad-exception-caught
            wait_for_logs(container, "Completed successfully", timeout=60)

        # Copy database file from container output to final location
        if container_db_path.exists():
            shutil.copy(container_db_path, db_path)
        else:
            raise FileNotFoundError(
                f"Database file not found at {container_db_path}. Check that profiles.yml path is correctly configured."
            )

    return db_path

class DuckDBTestCache:
    """Cache for DuckDB databases generated during integration tests."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cached_db(self, scenario: Scenario, flavor: str, version: str) -> Path | None:
        h = scenario.get_hash(flavor, version)
        cached_path = self.cache_dir / f"{h}.duckdb"
        if cached_path.exists():
            return cached_path
        return None

    def cache_db(self, scenario: Scenario, flavor: str, version: str, db_path: Path):
        h = scenario.get_hash(flavor, version)
        cached_path = self.cache_dir / f"{h}.duckdb"
        shutil.copy(db_path, cached_path)

@pytest.fixture(scope="session")
def dbt_duckdb_cache() -> DuckDBTestCache:
    """Fixture that provides a DuckDB database cache."""
    # Use a persistent cache directory if possible, otherwise a temporary one
    cache_dir = Path(".tests/cache/duckdb")
    return DuckDBTestCache(cache_dir)

@pytest.fixture(scope="session")
def dbt_duckdb_container(
    tmp_path_factory,
    dbt_config: tuple[str, str],
    scenario_name: str,
    dbt_duckdb_cache: DuckDBTestCache,
):  # pylint: disable=redefined-outer-name
    """Fixture that provides a DuckDB database path generated by running dbt build."""
    flavor, version = dbt_config
    scenario = registry.get(scenario_name)

    # Check cache first
    cached_db = dbt_duckdb_cache.get_cached_db(scenario, flavor, version)
    if cached_db:
        # Copy from cache to a temporary location for the current session
        tmp_dir = tmp_path_factory.mktemp(f"dbt_run_{flavor}_{version}_{scenario_name}")
        db_path = tmp_dir / "dev.duckdb"
        shutil.copy(cached_db, db_path)
        return db_path

    # Cache miss - build the database
    tmp_dir = tmp_path_factory.mktemp(f"dbt_run_{flavor}_{version}_{scenario_name}")
    db_path = tmp_dir / "dev.duckdb"

    use_docker = os.environ.get("USE_DOCKER", "false").lower() == "true"

    if use_docker:
        if not _docker_available():
            pytest.skip("Docker is not available or not running.")
        db_path = _run_dbt_docker(scenario, db_path, tmp_path_factory, flavor, version)
    else:
        if flavor != "core":
            pytest.skip(f"Local execution only supported for 'core' flavor. Flavor: {flavor}")
        db_path = _run_dbt_local(scenario, db_path, tmp_dir)

    # Store in cache
    dbt_duckdb_cache.cache_db(scenario, flavor, version, db_path)

    return db_path
