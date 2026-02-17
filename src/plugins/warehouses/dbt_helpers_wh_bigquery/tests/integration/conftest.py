"""Pytest fixtures for BigQuery integration tests using the goccy emulator."""

from pathlib import Path

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network
from testcontainers.core.waiting_utils import wait_for_logs


def _docker_available() -> bool:
    """Check if Docker is available and running."""
    try:
        import docker  # pylint: disable=import-outside-toplevel

        client = docker.from_env()
        client.ping()
        return True
    except Exception:  # pylint: disable=broad-exception-caught
        return False


@pytest.fixture(scope="session")
def bigquery_emulator():
    """Start the BigQuery emulator container, seed it with dbt, and yield connection config."""
    if not _docker_available():
        pytest.skip("Docker is not available or not running.")

    project_id = "test"
    dataset_id = "dataset1"
    emulator_alias = "bq-emulator"
    emulator_port = 9050

    with Network() as network:
        # 1. Start BigQuery Emulator
        emulator = (
            DockerContainer("ghcr.io/goccy/bigquery-emulator:latest")
            .with_command(["--project", project_id, "--dataset", dataset_id])
            .with_exposed_ports(emulator_port)
            .with_network(network)
            .with_network_aliases(emulator_alias)
        )

        with emulator:
            wait_for_logs(emulator, "REST server listening", timeout=30)

            # 2. Build and run dbt-runner to seed the emulator
            integration_dir = Path(__file__).parent
            dbt_runner = (
                DockerContainer("python:3.12-slim")
                .with_build_context(str(integration_dir))
                .with_dockerfile("Dockerfile")
                .with_network(network)
                .with_env("DBT_PROJECT", project_id)
                .with_env("DBT_DATASET", dataset_id)
                .with_env("DBT_BIGQUERY_HOST", emulator_alias)
                .with_env("DBT_BIGQUERY_PORT", str(emulator_port))
            )

            with dbt_runner:
                # Wait for dbt build to complete
                try:
                    # dbt logs "Finished running" when it's done
                    wait_for_logs(dbt_runner, "Finished running", timeout=60)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    # If log waiting fails, it might be because it finished too fast
                    print(f"Warning: wait_for_logs failed: {e}")

            # 3. Yield connection config for tests to use from host
            host = emulator.get_container_host_ip()
            port = emulator.get_exposed_port(emulator_port)
            api_endpoint = f"http://{host}:{port}"

            yield {
                "project": project_id,
                "api_endpoint": api_endpoint,
            }
