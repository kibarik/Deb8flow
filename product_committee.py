#!/usr/bin/env python3
"""
Product Committee Orchestrator

Simulates a virtual product committee by running four sequential debate rooms (TPM vs CPO/CFO/CTO/BDM)
using the existing document_debate_cli.py script, followed by TPM self-reflection.

Usage:
    python product_committee.py --prd <path> --question <text> [--model <name>]
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# --- Configuration Constants ---

DEFAULT_ROLES_DIR = "prompts/roles/"
DEFAULT_OUTPUT_DIR = "./committee_output"
DEFAULT_MAX_RETRIES = 2
DEFAULT_RUN_ID_FORMAT = "RUN_{timestamp}_{slug}"

# Room execution order (fixed for MVP)
ROOM_ORDER = ["cpo", "cfo", "cto", "bdm"]


# --- Logging Setup ---

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """
    Configure logging based on verbosity flags.

    Args:
        verbose: If True, set DEBUG level with detailed output
        quiet: If True, set WARNING level with minimal output
        If both False, set INFO level (normal)

    Returns:
        Configured logger instance
    """
    if quiet:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    elif verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s [%(name)s] - %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    return logger


# --- Argument Parsing ---

def parse_arguments() -> argparse.Namespace:
    """
    Parse and validate all CLI arguments.

    Returns:
        Parsed arguments namespace

    Raises:
        SystemExit if fatal validation fails
    """
    parser = argparse.ArgumentParser(
        description="Simulates a virtual product committee by running four sequential debate rooms.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Required arguments
    parser.add_argument(
        "--prd", "--docx",
        required=True,
        help="Path to PRD document (.docx or text file)",
    )
    parser.add_argument(
        "--question",
        required=True,
        help="Committee question for all rooms (e.g., 'What's the potential of this project?')",
    )

    # Optional arguments
    parser.add_argument(
        "--model",
        help="LLM model name (passed through to underlying debate CLI)",
        default=None,
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=f"Maximum retry attempts per room (default: {DEFAULT_MAX_RETRIES})",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Base output directory for run artifacts (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--roles-dir",
        default=DEFAULT_ROLES_DIR,
        help=f"Directory containing role prompt files (default: {DEFAULT_ROLES_DIR})",
    )
    parser.add_argument(
        "--run-id",
        help="Manual run identifier (auto-generated if omitted)",
        default=None,
    )
    parser.add_argument(
        "--allow-short-prd",
        action="store_true",
        help="Enforce minimum PRD length (100 chars); abort if shorter",
        default=False,
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (detailed retry attempts, CLI params, file sizes)",
        default=False,
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Enable quiet mode (minimal output: start/finish/errors only)",
        default=False,
    )

    args = parser.parse_args()

    # Validate arguments
    validate_arguments(args)

    return args


def validate_arguments(args: argparse.Namespace) -> None:
    """
    Validate CLI arguments and exit with appropriate error codes.

    Raises:
        SystemExit(1) if PRD file missing/unreadable
        SystemExit(1) if question is empty
        SystemExit(1) if TPM prompt file missing
    """
    # Check PRD file
    prd_path = Path(args.prd)
    if not prd_path.exists():
        logger.error(f"Error: PRD file not found or unreadable: {prd_path}")
        sys.exit(1)

    # Check question
    if not args.question or not args.question.strip():
        logger.error("Error: Question cannot be empty. Please provide a question for the committee.")
        sys.exit(1)

    # Check TPM prompt file
    tpm_prompt_path = Path(args.roles_dir) / "tpm.txt"
    if not tpm_prompt_path.exists():
        logger.error(f"Error: TPM prompt file not found at {tpm_prompt_path}. Aborting.")
        sys.exit(1)

    # Check mutual exclusivity
    if args.verbose and args.quiet:
        logger.error("Error: --verbose and --quiet are mutually exclusive. Please use only one.")
        sys.exit(1)

    # Check max_retries is non-negative
    if args.max_retries < 0:
        logger.error("Error: --max-retries must be >= 0")
        sys.exit(1)

    # Check PRD length if --allow-short-prd is set
    if args.allow_short_prd:
        prd_text = read_prd_text(prd_path)
        if len(prd_text) < 100:
            logger.error("Error: PRD is too short (< 100 characters) with --allow-short-prd flag.")
            sys.exit(1)

    logger.debug("All arguments validated successfully")


def read_prd_text(prd_path: Path) -> str:
    """
    Read PRD text from file for validation and logging purposes.

    Args:
        prd_path: Path to PRD file

    Returns:
        File content as string
    """
    try:
        with open(prd_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading PRD file: {e}")
        sys.exit(1)


def main():
    """Main entry point for the Product Committee Orchestrator."""

    # Parse arguments
    args = parse_arguments()

    # Setup logging
    logger = setup_logging(verbose=args.verbose, quiet=args.quiet)

    logger.info("Product Committee Orchestrator starting...")
    logger.info(f"PRD: {args.prd}")
    logger.info(f"Question: {args.question}")
    logger.info(f"Roles directory: {args.roles_dir}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Max retries: {args.max_retries}")

    logger.info("Configuration validated. Ready to orchestrate debate rooms.")
    logger.info("Note: Room execution not implemented in this foundational version.")
    logger.info("Next: Implement WP02 - Subprocess Wrapper & Retry Logic")


if __name__ == "__main__":
    main()
