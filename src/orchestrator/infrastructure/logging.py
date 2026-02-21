"""Logging infrastructure for orchestrator.

This module provides structured logging with file rotation,
console output, and automatic cleanup of old logs.
"""

import logging
import logging.handlers
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from src.orchestrator.domain.models import OrchestratorConfig


def setup_logging(config: OrchestratorConfig) -> logging.Logger:
    """Setup structured logging for orchestrator.

    Creates log directory, configures file handler with rotation,
    and optionally adds console handler for verbose mode.

    Args:
        config: Orchestrator configuration

    Returns:
        Configured logger instance
    """
    # Create log directory
    log_dir = Path(config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Clean up old logs
    _cleanup_old_logs(log_dir, days=7)

    # Get or create logger
    logger = logging.getLogger("orchestrator")
    logger.setLevel(logging.DEBUG)  # Capture all levels, handlers filter

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatters
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler with rotation
    log_filename = f"orchestrator-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    log_file_path = log_dir / log_filename

    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler (only in verbose mode)
    if config.verbose:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Set baseline level
    logger.setLevel(logging.DEBUG if config.verbose else logging.INFO)

    logger.info(f"Logging initialized: {log_file_path}")
    return logger


def _cleanup_old_logs(log_dir: Path, days: int = 7) -> None:
    """Remove log files older than specified days.

    Args:
        log_dir: Directory containing log files
        days: Number of days after which logs are removed
    """
    if not log_dir.exists():
        return

    cutoff_time = time.time() - (days * 24 * 60 * 60)

    for log_file in log_dir.glob("orchestrator-*.log*"):
        try:
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                # Also remove corresponding .rotated files if any
                for rotated in log_file.parent.glob(f"{log_file.name}.*"):
                    rotated.unlink()
        except Exception as e:
            # Log cleanup errors shouldn't crash the app
            print(f"Warning: Failed to clean up old log {log_file}: {e}")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance for orchestrator modules.

    Args:
        name: Logger name (defaults to "orchestrator")

    Returns:
        Logger instance
    """
    if name is None:
        name = "orchestrator"
    return logging.getLogger(f"orchestrator.{name}")


class PhaseContext:
    """Context manager for adding phase context to log messages.

    Example:
        with PhaseContext(logger, "specify"):
            logger.info("Starting phase")
            # Logs: "[specify] Starting phase"
    """

    def __init__(self, logger: logging.Logger, phase_name: str):
        """Initialize phase context.

        Args:
            logger: Logger instance
            phase_name: Name of the phase
        """
        self.logger = logger
        self.phase_name = phase_name
        self.old_extra = None

    def __enter__(self):
        """Add phase context to logger."""
        # Store old extra if exists
        if hasattr(self.logger, "extra"):
            self.old_extra = self.logger.extra
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Remove phase context from logger."""
        if self.old_extra is not None:
            self.logger.extra = self.old_extra
        return False


class PhaseAdapter(logging.LoggerAdapter):
    """Logger adapter that adds phase context to messages.

    Example:
        adapter = PhaseAdapter(logger, {"phase": "specify"})
        adapter.info("Starting phase")
        # Logs: "[specify] Starting phase"
    """

    def __init__(self, logger: logging.Logger, extra: dict):
        """Initialize phase adapter.

        Args:
            logger: Base logger
            extra: Extra context to add to messages
        """
        super().__init__(logger, extra)
        self.extra = extra

    def process(self, msg, kwargs):
        """Add phase context to message.

        Args:
            msg: Original message
            kwargs: Logging keyword arguments

        Returns:
            Tuple of (modified_message, modified_kwargs)
        """
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"].update(self.extra)
        return f"[{self.extra.get('phase', '?')}] {msg}", kwargs
