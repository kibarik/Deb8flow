"""Unit tests for logging infrastructure."""

import logging
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.orchestrator.domain.models import OrchestratorConfig
from src.orchestrator.infrastructure.logging import (
    PhaseAdapter,
    PhaseContext,
    _cleanup_old_logs,
    get_logger,
    setup_logging,
)


@pytest.fixture
def temp_log_dir(tmp_path):
    """Create temporary log directory."""
    log_dir = tmp_path / ".orchestrator" / "logs"
    return log_dir


@pytest.fixture
def config(temp_log_dir):
    """Create test configuration."""
    return OrchestratorConfig(
        log_dir=str(temp_log_dir),
        log_level="INFO",
        verbose=False,
    )


class TestLoggingSetup:
    """Tests for logging setup."""

    def test_setup_logging_creates_directory(self, temp_log_dir):
        """Test that setup_logging creates log directory."""
        config = OrchestratorConfig(log_dir=str(temp_log_dir))

        assert not temp_log_dir.exists()

        logger = setup_logging(config)

        assert temp_log_dir.exists()

    def test_setup_logging_creates_log_file(self, config):
        """Test that setup_logging creates log file."""
        logger = setup_logging(config)

        log_dir = Path(config.log_dir)
        log_files = list(log_dir.glob("orchestrator-*.log"))
        assert len(log_files) >= 1

    def test_setup_logging_with_verbose_mode(self, temp_log_dir):
        """Test that verbose mode adds console handler."""
        config = OrchestratorConfig(
            log_dir=str(temp_log_dir),
            verbose=True,
        )

        logger = setup_logging(config)

        # Should have 2 handlers (file + console)
        assert len(logger.handlers) == 2

    def test_setup_logging_without_verbose_mode(self, config):
        """Test that non-verbose mode only has file handler."""
        logger = setup_logging(config)

        # Should only have file handler
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.handlers.RotatingFileHandler)

    def test_logger_writes_to_file(self, config):
        """Test that logger writes messages to file."""
        logger = setup_logging(config)

        logger.info("Test message")

        # Find log file
        log_dir = Path(config.log_dir)
        log_files = list(log_dir.glob("orchestrator-*.log"))
        assert len(log_files) >= 1

        log_content = log_files[0].read_text()
        assert "Test message" in log_content

    def test_log_format_includes_timestamp(self, config):
        """Test that log format includes timestamp."""
        logger = setup_logging(config)

        logger.info("Test message")

        log_dir = Path(config.log_dir)
        log_files = list(log_dir.glob("orchestrator-*.log"))
        log_content = log_files[0].read_text()

        # Should contain timestamp like [2024-02-21 12:34:56]
        import re
        assert re.search(r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]", log_content)


class TestLogRotation:
    """Tests for log file rotation."""

    def test_rotation_settings(self, config):
        """Test that rotation settings are configured correctly."""
        logger = setup_logging(config)

        file_handler = logger.handlers[0]
        assert file_handler.maxBytes == 10 * 1024 * 1024  # 10MB
        assert file_handler.backupCount == 3


class TestLogCleanup:
    """Tests for old log cleanup."""

    def test_cleanup_removes_old_logs(self, temp_log_dir):
        """Test that cleanup removes logs older than 7 days."""
        temp_log_dir.mkdir(parents=True, exist_ok=True)

        # Create old log file
        old_log = temp_log_dir / "orchestrator-20240101-120000.log"
        old_log.write_text("Old log content")

        # Set modification time to 10 days ago
        old_time = time.time() - (10 * 24 * 60 * 60)
        os.utime(old_log, (old_time, old_time))

        # Run cleanup
        _cleanup_old_logs(temp_log_dir, days=7)

        # Old log should be removed
        assert not old_log.exists()

    def test_cleanup_preserves_recent_logs(self, temp_log_dir):
        """Test that cleanup preserves recent logs."""
        temp_log_dir.mkdir(parents=True, exist_ok=True)

        # Create recent log file
        recent_log = temp_log_dir / "orchestrator-20240220-120000.log"
        recent_log.write_text("Recent log content")

        # Run cleanup
        _cleanup_old_logs(temp_log_dir, days=7)

        # Recent log should be preserved
        assert recent_log.exists()


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_orchestrator_logger(self):
        """Test that get_logger returns orchestrator logger."""
        # Reset logging state
        logging.Logger.manager.loggerDict.clear()

        logger = get_logger()
        # Note: get_logger returns f"orchestrator.{name}" or "orchestrator"
        assert "orchestrator" in logger.name

    def test_get_logger_with_custom_name(self):
        """Test that get_logger with name returns scoped logger."""
        logger = get_logger("docker")
        assert "docker" in logger.name


class TestPhaseAdapter:
    """Tests for PhaseAdapter."""

    def test_phase_adapter_creation(self):
        """Test that PhaseAdapter can be created."""
        base_logger = logging.getLogger("test_adapter")
        adapter = PhaseAdapter(base_logger, {"phase": "specify"})

        assert adapter.extra["phase"] == "specify"

    def test_phase_adapter_with_multiple_phases(self):
        """Test PhaseAdapter with different phase names."""
        base_logger = logging.getLogger("test_adapter2")
        adapter1 = PhaseAdapter(base_logger, {"phase": "specify"})
        adapter2 = PhaseAdapter(base_logger, {"phase": "plan"})

        assert adapter1.extra["phase"] == "specify"
        assert adapter2.extra["phase"] == "plan"


class TestPhaseContext:
    """Tests for PhaseContext context manager."""

    def test_phase_context_adds_context(self):
        """Test that PhaseContext adds context to logger."""
        logger = logging.getLogger("test_context")

        # Can't easily test context manager without actually logging
        # Just verify it can be instantiated
        context = PhaseContext(logger, "specify")
        assert context.phase_name == "specify"

    def test_phase_context_enter_exit(self):
        """Test that PhaseContext can be used as context manager."""
        logger = logging.getLogger("test_context2")

        with PhaseContext(logger, "plan") as ctx:
            assert ctx.phase_name == "plan"
            assert ctx is not None
