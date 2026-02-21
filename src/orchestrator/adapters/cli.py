"""CLI argument parser for orchestrator command.

This module handles command-line argument parsing and validation
for the orchestrator tool.
"""

import argparse
import logging
import signal
import sys
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Global shutdown flag for signal handling
_shutdown_requested = False


def signal_handler(signum, frame):
    """Handle SIGINT/SIGTERM for graceful shutdown.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    global _shutdown_requested
    _shutdown_requested = True
    print("\n[ORCHESTRATOR] Interrupted by user. Shutting down...")


def is_shutdown_requested() -> bool:
    """Check if shutdown has been requested.

    Returns:
        True if SIGINT/SIGTERM was received
    """
    return _shutdown_requested


def parse_args(argv=None) -> Dict[str, Any]:
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:])

    Returns:
        Dictionary of parsed arguments

    Raises:
        FileNotFoundError: If source or corrections files don't exist
    """
    parser = argparse.ArgumentParser(
        prog="orchestrator",
        description="Automated Spec-Kitty workflow orchestration via Docker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.md corrections.md
  %(prog)s document.md corrections.md --output ./output
  %(prog)s document.md corrections.md --max-retries 5 --verbose
  %(prog)s document.md corrections.md --dry-run
        """,
    )

    # Positional arguments
    parser.add_argument(
        "source",
        type=Path,
        help="Path to source document to process",
    )
    parser.add_argument(
        "corrections",
        type=Path,
        help="Path to corrections document",
    )

    # Optional arguments
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output directory for corrected file (default: same as source)",
    )

    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=None,
        help="Path to config file (default: config/debate_config.yaml)",
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=None,
        help="Maximum retry attempts per phase (default: 3)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Container timeout in seconds (default: 3600)",
    )

    parser.add_argument(
        "--keep-containers",
        action="store_true",
        help="Don't stop containers after completion (for debugging)",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration without executing workflow",
    )

    args = parser.parse_args(argv)

    # Validate arguments
    _validate_arguments(args)

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    return vars(args)


def _validate_arguments(args: argparse.Namespace) -> None:
    """Validate CLI arguments.

    Args:
        args: Parsed arguments

    Raises:
        FileNotFoundError: If required files don't exist
        ValueError: If argument values are invalid
    """
    # Validate source file exists
    if not args.source.exists():
        raise FileNotFoundError(
            f"Source file not found: {args.source}\n"
            f"Please check the path and try again."
        )

    if not args.source.is_file():
        raise ValueError(
            f"Source path is not a file: {args.source}"
        )

    # Validate source file is readable
    try:
        with open(args.source, "r") as f:
            f.read(1)  # Try to read first byte
    except PermissionError:
        raise PermissionError(
            f"Source file is not readable: {args.source}"
        )

    # Validate corrections file exists
    if not args.corrections.exists():
        raise FileNotFoundError(
            f"Corrections file not found: {args.corrections}\n"
            f"Please check the path and try again."
        )

    if not args.corrections.is_file():
        raise ValueError(
            f"Corrections path is not a file: {args.corrections}"
        )

    # Validate corrections file is readable
    try:
        with open(args.corrections, "r") as f:
            f.read(1)
    except PermissionError:
        raise PermissionError(
            f"Corrections file is not readable: {args.corrections}"
        )

    # Validate output directory if specified
    if args.output is not None:
        if args.output.exists() and not args.output.is_dir():
            raise ValueError(
                f"Output path exists but is not a directory: {args.output}"
            )
        # Create output directory if it doesn't exist
        args.output.mkdir(parents=True, exist_ok=True)

    # Validate numeric arguments
    if args.max_retries is not None and args.max_retries < 0:
        raise ValueError(
            f"max-retries must be >= 0, got {args.max_retries}"
        )

    if args.timeout is not None and args.timeout < 1:
        raise ValueError(
            f"timeout must be >= 1, got {args.timeout}"
        )
