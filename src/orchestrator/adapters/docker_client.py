"""Docker client adapter for container lifecycle management.

This module provides a wrapper around the Docker Python SDK with
orchestration-specific functionality including health checks, log
streaming, and resource management.
"""

import logging
import signal
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Optional, Tuple

import docker
from docker.errors import DockerException, ImageNotFound, APIError

from src.orchestrator.domain.models import OrchestratorConfig

logger = logging.getLogger(__name__)


class DockerUnavailableError(Exception):
    """Raised when Docker daemon is not available."""

    pass


class DockerImageError(Exception):
    """Raised when Docker image operations fail."""

    pass


class DockerClient:
    """Wrapper for Docker SDK with orchestration-specific functionality.

    This class manages Docker container lifecycle including:
    - Container creation with volume mounts and resource limits
    - Health checking with configurable timeout
    - Real-time log streaming
    - Automatic cleanup on exit

    Example:
        with DockerClient(config) as client:
            container_id = client.start(source_path, workdir)
            # Container is automatically stopped on context exit
    """

    def __init__(self, config: OrchestratorConfig):
        """Initialize Docker client.

        Args:
            config: Orchestrator configuration
        """
        self.config = config
        self._client: Optional[docker.DockerClient] = None
        self._container: Optional[docker.models.containers.Container] = None
        self._log_future: Optional[Future] = None
        self._executor: Optional[ThreadPoolExecutor] = None
        self._lock = threading.Lock()

    def __enter__(self) -> "DockerClient":
        """Enter context manager and initialize Docker client.

        Returns:
            Self for method chaining
        """
        try:
            self._client = docker.from_env()
            return self
        except DockerException as e:
            raise DockerUnavailableError(
                f"Failed to connect to Docker daemon: {e}"
            )

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and cleanup resources.

        Ensures container is stopped and removed even on exception.
        """
        self.stop()
        if self._client:
            self._client.close()
            self._client = None

    def is_available(self) -> Tuple[bool, str]:
        """Check if Docker daemon is available.

        Returns:
            Tuple of (is_available, error_message)
        """
        try:
            client = docker.from_env()
            client.ping()
            return True, ""
        except DockerException as e:
            return False, f"Docker daemon not available: {e}"

    def check_image(self) -> Tuple[bool, str]:
        """Check if required Docker image exists, pull if needed.

        Returns:
            Tuple of (success, message)

        Raises:
            DockerImageError: If image check/pull fails critically
        """
        if not self._client:
            raise DockerUnavailableError("Docker client not initialized")

        try:
            # Try to get the image
            self._client.images.get(self.config.docker_image)
            logger.info(f"Using cached image: {self.config.docker_image}")
            return True, "cached"

        except ImageNotFound:
            # Image not found, try to pull
            logger.info(f"Pulling image: {self.config.docker_image}")
            try:
                self._client.images.pull(self.config.docker_image)
                logger.info(f"Successfully pulled image: {self.config.docker_image}")
                return True, "pulled"
            except APIError as e:
                raise DockerImageError(
                    f"Failed to pull image {self.config.docker_image}: {e}"
                )

        except APIError as e:
            raise DockerImageError(
                f"Docker API error checking image: {e}"
            )

    def start(self, source_path: Path, workdir: Path) -> str:
        """Start a Docker container with the specified configuration.

        Args:
            source_path: Path to source document (mounted into container)
            workdir: Working directory to mount as /workspace

        Returns:
            Container ID

        Raises:
            DockerUnavailableError: If Docker is not available
            DockerImageError: If required image is not available
        """
        if not self._client:
            raise DockerUnavailableError("Docker client not initialized")

        # Check image availability
        image_status, msg = self.check_image()
        if not image_status:
            raise DockerImageError(
                f"Cannot start container: {msg}"
            )

        # Generate unique container name
        timestamp = int(time.time())
        unique_id = uuid.uuid4().hex[:8]
        container_name = f"claude-orchestrator-{timestamp}-{unique_id}"

        # Prepare volume mounts
        volumes = {str(workdir): {"bind": "/workspace", "mode": "rw"}}

        # Prepare environment variables
        environment = {}
        if "CLAUDE_API_KEY" in self._client.api.config:
            environment["CLAUDE_API_KEY"] = self._client.api.config["CLAUDE_API_KEY"]

        # Prepare resource limits
        host_config = {}
        if self.config.container_memory_limit:
            host_config["mem_limit"] = self.config.container_memory_limit
        if self.config.container_cpu_quota:
            host_config["cpu_quota"] = int(self.config.container_cpu_quota * 100000)
            host_config["cpu_period"] = 100000

        logger.info(f"Starting container: {container_name}")

        try:
            self._container = self._client.containers.run(
                image=self.config.docker_image,
                name=container_name,
                volumes=volumes,
                environment=environment,
                detach=True,
                remove=False,  # We manage removal
                **host_config,
            )

            container_id = self._container.id
            logger.info(f"Container started: {container_id}")

            return container_id

        except APIError as e:
            raise DockerImageError(
                f"Failed to start container: {e}"
            )

    def health_check(self) -> bool:
        """Poll container status until ready or timeout.

        Returns:
            True if container is running, False if timeout

        Raises:
            DockerUnavailableError: If container not started
        """
        if not self._container:
            raise DockerUnavailableError("No container to check")

        start_time = time.time()
        timeout = self.config.container_timeout

        logger.info("Waiting for container to be ready...")

        while time.time() - start_time < timeout:
            try:
                self._container.reload()
                status = self._container.status

                if status == "running":
                    logger.info("Container is ready")
                    return True
                elif status in ("exited", "dead"):
                    logger.error(f"Container exited unexpectedly: {status}")
                    return False

            except APIError:
                pass

            time.sleep(1)

        logger.warning("Container health check timed out")
        return False

    def stream_logs(self, callback: Callable[[str], None]) -> None:
        """Start streaming container logs in background thread.

        Args:
            callback: Function to call with each log line

        Raises:
            DockerUnavailableError: If container not started
        """
        if not self._container:
            raise DockerUnavailableError("No container to stream logs from")

        if not self._executor:
            self._executor = ThreadPoolExecutor(max_workers=1)

        def _stream_worker():
            try:
                for line in self._container.logs(stream=True, follow=True):
                    callback(line.decode("utf-8").rstrip())
            except Exception as e:
                logger.error(f"Error streaming logs: {e}")

        self._log_future = self._executor.submit(_stream_worker)
        logger.debug("Log streaming started")

    def stop(self, force: bool = False) -> None:
        """Stop and remove the container.

        Args:
            force: If True, kill container instead of graceful stop
        """
        with self._lock:
            # Stop log streaming
            if self._log_future:
                if self._log_future.running():
                    self._log_future.cancel()
                self._log_future = None

            if self._executor:
                self._executor.shutdown(wait=False)
                self._executor = None

            # Stop and remove container
            if self._container:
                try:
                    logger.info(f"Stopping container: {self._container.id}")

                    if force:
                        self._container.kill()
                    else:
                        self._container.stop(timeout=10)

                    self._container.remove(force=True)
                    logger.info("Container stopped and removed")

                except Exception as e:
                    logger.warning(f"Error stopping container: {e}")
                finally:
                    self._container = None
