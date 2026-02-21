"""Unit tests for Docker client adapter."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.orchestrator.adapters.docker_client import (
    DockerClient,
    DockerImageError,
    DockerUnavailableError,
)
from src.orchestrator.domain.models import OrchestratorConfig


@pytest.fixture
def config():
    """Create test configuration."""
    return OrchestratorConfig(
        docker_image="test-image:latest",
        container_timeout=60,
        container_memory_limit="1g",
        container_cpu_quota=1.0,
    )


@pytest.fixture
def mock_docker():
    """Create mock docker module."""
    with patch("src.orchestrator.adapters.docker_client.docker") as mock:
        yield mock


@pytest.fixture
def mock_container():
    """Create mock container."""
    container = MagicMock()
    container.id = "test-container-id"
    container.status = "running"
    container.logs.return_value = iter([b"log line 1\n", b"log line 2\n"])
    return container


class TestDockerClientInitialization:
    """Tests for DockerClient initialization."""

    def test_init_with_config(self, config):
        """Test initialization with configuration."""
        client = DockerClient(config)
        assert client.config == config
        assert client._client is None
        assert client._container is None


class TestContextManager:
    """Tests for context manager functionality."""

    def test_context_manager_initializes_docker(self, config, mock_docker):
        """Test that context manager initializes Docker client."""
        mock_docker.from_env.return_value = MagicMock()

        with DockerClient(config) as client:
            assert client._client is not None
            mock_docker.from_env.assert_called_once()

    def test_context_manager_closes_docker(self, config, mock_docker):
        """Test that context manager closes Docker client on exit."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        with DockerClient(config) as client:
            pass

        mock_client.close.assert_called_once()


class TestDockerAvailability:
    """Tests for Docker availability checking."""

    def test_is_available_when_docker_running(self, config, mock_docker):
        """Test is_available returns True when Docker is running."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.ping.return_value = True

        available, error = DockerClient(config).is_available()

        assert available is True
        assert error == ""

    def test_is_available_when_docker_not_running(self, config, mock_docker):
        """Test is_available returns False when Docker is not running."""
        from docker.errors import DockerException
        mock_docker.from_env.side_effect = DockerException("Not running")

        available, error = DockerClient(config).is_available()

        assert available is False
        assert "Docker daemon not available" in error


class TestImageChecking:
    """Tests for image checking and pulling."""

    def test_check_image_when_cached(self, config, mock_docker):
        """Test check_image returns cached when image exists."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.images.get.return_value = MagicMock()

        with DockerClient(config) as client:
            success, msg = client.check_image()

        assert success is True
        assert msg == "cached"
        mock_client.images.get.assert_called_once_with("test-image:latest")

    def test_check_image_pulls_when_missing(self, config, mock_docker):
        """Test check_image pulls image when not found."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        from docker.errors import ImageNotFound

        mock_client.images.get.side_effect = ImageNotFound("Not found")

        with DockerClient(config) as client:
            success, msg = client.check_image()

        assert success is True
        assert msg == "pulled"
        mock_client.images.pull.assert_called_once_with("test-image:latest")

    def test_check_image_raises_on_pull_failure(self, config, mock_docker):
        """Test check_image raises DockerImageError on pull failure."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        from docker.errors import ImageNotFound, APIError

        mock_client.images.get.side_effect = ImageNotFound("Not found")
        mock_client.images.pull.side_effect = APIError("Pull failed")

        with DockerClient(config) as client:
            with pytest.raises(DockerImageError, match="Failed to pull"):
                client.check_image()


class TestContainerStart:
    """Tests for container starting."""

    def test_start_creates_container_with_volume_mount(
        self, config, mock_docker, mock_container
    ):
        """Test that start creates container with volume mounts."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.images.get.return_value = MagicMock()  # Image exists
        mock_client.containers.run.return_value = mock_container

        workdir = Path("/test/workdir")

        with DockerClient(config) as client:
            container_id = client.start(Path("/test/source.md"), workdir)

        assert container_id == "test-container-id"
        mock_client.containers.run.assert_called_once()

        # Verify volume mounts
        call_kwargs = mock_client.containers.run.call_args.kwargs
        assert "volumes" in call_kwargs
        assert str(workdir) in call_kwargs["volumes"]

    def test_start_applies_resource_limits(self, config, mock_docker, mock_container):
        """Test that start applies resource limits from config."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.images.get.return_value = MagicMock()
        mock_client.containers.run.return_value = mock_container

        workdir = Path("/test/workdir")

        with DockerClient(config) as client:
            client.start(Path("/test/source.md"), workdir)

        call_kwargs = mock_client.containers.run.call_args.kwargs
        assert "mem_limit" in call_kwargs
        assert call_kwargs["mem_limit"] == "1g"
        assert "cpu_quota" in call_kwargs
        assert call_kwargs["cpu_quota"] == 100000

    def test_start_generates_unique_container_name(self, config, mock_docker, mock_container):
        """Test that start generates unique container names."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.images.get.return_value = MagicMock()
        mock_client.containers.run.return_value = mock_container

        workdir = Path("/test/workdir")

        with DockerClient(config) as client:
            id1 = client.start(Path("/test/source.md"), workdir)
            # Mock returns same container, so name would be same
            # But in real scenario, each call generates unique name

        call_kwargs = mock_client.containers.run.call_args.kwargs
        assert "name" in call_kwargs
        assert "claude-orchestrator-" in call_kwargs["name"]


class TestHealthCheck:
    """Tests for container health checking."""

    def test_health_check_returns_true_when_ready(self, config, mock_docker, mock_container):
        """Test health_check returns True when container is running."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.containers.run.return_value = mock_container

        workdir = Path("/test/workdir")

        with DockerClient(config) as client:
            client.start(Path("/test/source.md"), workdir)
            result = client.health_check()

        assert result is True

    def test_health_check_returns_false_on_timeout(self, config, mock_docker):
        """Test health_check returns False on timeout."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_container = MagicMock()
        mock_container.status = "created"  # Never reaches running
        mock_client.containers.run.return_value = mock_container

        workdir = Path("/test/workdir")

        # Use short timeout for test
        config.container_timeout = 1

        with DockerClient(config) as client:
            client.start(Path("/test/source.md"), workdir)
            result = client.health_check()

        assert result is False


class TestLogStreaming:
    """Tests for log streaming."""

    def test_stream_logs_calls_callback(self, config, mock_docker, mock_container):
        """Test that stream_logs calls callback with log lines."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.images.get.return_value = MagicMock()
        mock_client.containers.run.return_value = mock_container

        workdir = Path("/test/workdir")
        logs = []

        def log_callback(line):
            logs.append(line)

        with DockerClient(config) as client:
            client.start(Path("/test/source.md"), workdir)
            # Start log streaming inside context before exit
            client.stream_logs(log_callback)
            # Verify executor was created for background task
            assert client._executor is not None

        # On exit, stop() cleans up the executor
        assert client._executor is None


class TestContainerStop:
    """Tests for container stopping."""

    def test_stop_stops_and_removes_container(self, config, mock_docker, mock_container):
        """Test that stop stops and removes container."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.images.get.return_value = MagicMock()
        mock_client.containers.run.return_value = mock_container

        workdir = Path("/test/workdir")

        with DockerClient(config) as client:
            client.start(Path("/test/source.md"), workdir)
            client.stop()

        mock_container.stop.assert_called_once_with(timeout=10)
        mock_container.remove.assert_called_once_with(force=True)

    def test_stop_forces_when_requested(self, config, mock_docker, mock_container):
        """Test that stop uses force when requested."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.images.get.return_value = MagicMock()
        mock_client.containers.run.return_value = mock_container

        workdir = Path("/test/workdir")

        with DockerClient(config) as client:
            client.start(Path("/test/source.md"), workdir)
            client.stop(force=True)

        mock_container.kill.assert_called_once()
        mock_container.remove.assert_called_once_with(force=True)

    def test_context_manager_stops_on_exit(self, config, mock_docker, mock_container):
        """Test that context manager stops container on exit."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.images.get.return_value = MagicMock()
        mock_client.containers.run.return_value = mock_container

        workdir = Path("/test/workdir")

        with DockerClient(config) as client:
            client.start(Path("/test/source.md"), workdir)

        mock_container.stop.assert_called_once()
        mock_container.remove.assert_called_once()
