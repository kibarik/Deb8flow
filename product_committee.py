#!/usr/bin/env python3
"""
Product Committee Orchestrator (Clean Architecture)

Simulates a virtual product committee by running four debate rooms
(TPM vs CPO/CFO/CTO/BDM) using the refactored clean architecture system.

Usage:
    python3 product_committee.py --prd <path> --question <text> [--model <name>]
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from src.committee.application.run_committee import RunProductCommittee
from src.committee.adapters.reports.final_report import FinalReportGenerator
from src.committee.adapters.reports.conclusion import ConclusionGenerator
from src.shared.debate.infrastructure.executors.cli_executor import CliDebateExecutor
from src.shared.debate.infrastructure.storage.local_storage import LocalFileStorage
from pydantic import BaseModel, Field, field_validator


logger = logging.getLogger(__name__)


# Configuration constants
DEFAULT_ROLES_DIR = "prompts/roles/"
DEFAULT_OUTPUT_DIR = "./committee_output"
DEFAULT_MAX_RETRIES = 2
DEFAULT_MAX_CONCURRENCY = 2
MIN_CONCURRENCY = 0
MAX_CONCURRENCY = 4


class CommitteeCliInput(BaseModel):
    """Validated CLI input for product committee."""
    prd_path: Path = Field(..., description="Path to PRD document")
    question: str = Field(..., min_length=1)
    model: Optional[str] = None
    language: Optional[str] = None
    max_retries: int = Field(DEFAULT_MAX_RETRIES, ge=0)
    max_concurrency: int = Field(DEFAULT_MAX_CONCURRENCY, ge=MIN_CONCURRENCY, le=MAX_CONCURRENCY)
    output_dir: Path = Field(Path(DEFAULT_OUTPUT_DIR))
    roles_dir: Path = Field(Path(DEFAULT_ROLES_DIR))
    run_id: Optional[str] = None
    verbose: bool = False
    quiet: bool = False

    @field_validator("prd_path")
    @classmethod
    def validate_prd_exists(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"PRD file not found: {v}")
        return v

    @field_validator("roles_dir")
    @classmethod
    def validate_roles_dir(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"Roles directory not found: {v}")
        tpm_prompt = v / "tpm.txt"
        if not tpm_prompt.exists():
            raise ValueError(f"Required TPM prompt file not found: {tpm_prompt}")
        return v

    @field_validator("question")
    @classmethod
    def validate_question_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty")
        return v


def parse_arguments() -> CommitteeCliInput:
    """Parse and validate CLI arguments."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Product Committee Orchestrator (Clean Architecture)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--prd", required=True, help="Path to PRD document")
    parser.add_argument("--question", required=True, help="Committee question")
    parser.add_argument("--model", help="LLM model name")
    parser.add_argument("--language", help="Language for output")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES, help="Max retry attempts")
    parser.add_argument("--max-concurrency", type=int, default=DEFAULT_MAX_CONCURRENCY, help="Max parallel rooms (0=all)")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--roles-dir", default=DEFAULT_ROLES_DIR, help="Roles directory")
    parser.add_argument("--run-id", help="Manual run identifier")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode")

    args = parser.parse_args()

    # Convert to CommitteeCliInput
    try:
        return CommitteeCliInput(
            prd_path=Path(args.prd),
            question=args.question,
            model=args.model,
            language=args.language,
            max_retries=args.max_retries,
            max_concurrency=args.max_concurrency,
            output_dir=Path(args.output_dir),
            roles_dir=Path(args.roles_dir),
            run_id=args.run_id,
            verbose=args.verbose,
            quiet=args.quiet
        )
    except Exception as e:
        parser.error(str(e))
        sys.exit(1)


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging based on verbosity flags."""
    if quiet:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    elif verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class ReportGeneratorAdapter:
    """Adapter combining both report generators."""
    def __init__(self):
        self.final_gen = FinalReportGenerator()
        self.conclusion_gen = ConclusionGenerator()

    def generate_final_report(self, run_id: str, prd_path: str, question: str, rooms, metadata: dict) -> str:
        return self.final_gen.generate_final_report(run_id, prd_path, question, rooms, metadata)

    def generate_conclusion(self, question: str, rooms, metadata: dict) -> str:
        return self.conclusion_gen.generate_conclusion(question, rooms, metadata)

    def generate_intermediate_report(self, run_id: str, completed_rooms, total_rooms: int) -> str:
        return self.final_gen.generate_intermediate_report(run_id, completed_rooms, total_rooms)


async def main_async() -> int:
    """Main async entry point."""
    # Parse and validate arguments
    cli_input = parse_arguments()

    # Setup logging
    setup_logging(verbose=cli_input.verbose, quiet=cli_input.quiet)

    logger.info("Product Committee Orchestrator starting...")
    logger.info(f"PRD: {cli_input.prd_path}")
    logger.info(f"Question: {cli_input.question}")

    # Create infrastructure adapters
    executor = CliDebateExecutor()
    storage = LocalFileStorage()
    generator = ReportGeneratorAdapter()

    # Create use case
    use_case = RunProductCommittee(executor, generator, storage)

    # Execute committee
    try:
        result = await use_case.execute(
            prd_path=str(cli_input.prd_path),
            question=cli_input.question,
            roles_dir=str(cli_input.roles_dir),
            model=cli_input.model,
            language=cli_input.language,
            max_retries=cli_input.max_retries,
            max_concurrency=cli_input.max_concurrency,
            output_dir=cli_input.output_dir,
            manual_run_id=cli_input.run_id
        )

        logger.info(f"Product Committee Orchestrator completed successfully!")
        logger.info(f"Run ID: {result.run_id.value}")
        logger.info(f"Output directory: {cli_input.output_dir}/{result.run_id.value}")

        # Exit with error code if any rooms failed
        if result.failed_rooms:
            logger.warning(f"{len(result.failed_rooms)} room(s) failed. Check metadata.json for details.")
            return 1

        return 0

    except Exception as e:
        logger.error(f"Error during execution: {e}")
        if cli_input.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    try:
        exit_code = asyncio.run(main_async())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
