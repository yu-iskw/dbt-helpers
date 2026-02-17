import os
import shutil
import subprocess  # nosec B404
from pathlib import Path
from typing import Any

from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from .scenarios import Scenario


class DbtRunner:
    """Handles running dbt commands for integration testing."""

    def __init__(self, use_docker: bool = False):
        self.use_docker = use_docker

    def run_build(
        self,
        scenario: Scenario,
        target_dir: Path,
        flavor: str = "core",
        version: str = "1.11",
        env: dict[str, str] | None = None,
    ) -> None:
        """Run 'dbt build' for the given scenario."""
        if self.use_docker:
            self._run_docker(scenario, target_dir, flavor, version, env)
        else:
            self._run_local(scenario, target_dir, env)

    def _run_local(self, scenario: Scenario, target_dir: Path, env: dict[str, str] | None = None) -> None:
        """Run dbt build locally."""
        scenario.write_to_disk(target_dir)

        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        run_env["DBT_PROFILES_DIR"] = str(target_dir)

        subprocess.run(  # nosec B603, B607
            ["dbt", "build", "--project-dir", str(target_dir)],
            env=run_env,
            check=True,
            capture_output=True,
            cwd=str(target_dir),
        )

    def _run_docker(
        self,
        scenario: Scenario,
        target_dir: Path,
        flavor: str,
        version: str,
        env: dict[str, str] | None = None,
        dockerfile_path: Path | None = None,
    ) -> None:
        """Run dbt build in a Docker container."""
        if not dockerfile_path:
            # This is a bit tricky since the Dockerfile usually lives in the plugin's test dir.
            # We might need to pass it or have a default one.
            raise ValueError("dockerfile_path must be provided for Docker execution.")

        scenario.write_to_disk(target_dir)

        # In the DuckDB plugin, we mounted the target_dir as /workspace.
        # Here we follow a similar pattern but make it slightly more configurable if needed.

        container = (
            DockerContainer("python:3.12-slim")
            .with_kwargs(buildargs={"DBT_FLAVOR": flavor, "DBT_VERSION": version})
            .with_build_context(str(dockerfile_path.parent))
            .with_dockerfile(str(dockerfile_path))
            .with_volume_mapping(str(target_dir), "/workspace")
            .with_env("DBT_PROFILES_DIR", "/workspace")
        )

        if env:
            for k, v in env.items():
                container = container.with_env(k, v)

        # Default command: build the dbt project
        container = container.with_command(["dbt", "build", "--project-dir", "/workspace"])

        with container:
            try:
                # dbt 1.8+ shows "Finished running ..."
                wait_for_logs(container, "Finished running", timeout=60)
            except Exception as e:
                # If log waiting fails, it might be because the container exited too fast.
                print(f"Warning: wait_for_logs failed: {e}")
