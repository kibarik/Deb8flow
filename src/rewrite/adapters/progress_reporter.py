"""
Progress reporter for rewrite operations.

Provides structured console output for tracking rewrite progress.
"""
import logging
from typing import List, Optional
from pathlib import Path

from ..domain.entities import RevisionItem, RewriteResult
from ..domain.value_objects import RewriteStatus


logger = logging.getLogger(__name__)


class ProgressReporter:
    """
    Reports progress of rewrite operations to console.

    Uses structured logging with prefixes for easy parsing:
    - [REWRITE]: General rewrite operations
    - [DEBATE]: Debate verification rounds
    - [JUDGE]: Judge verdicts
    """

    PREFIX_REWRITE = "[REWRITE]"
    PREFIX_DEBATE = "[DEBATE]"
    PREFIX_JUDGE = "[JUDGE]"

    def __init__(self, verbose: bool = False):
        """
        Initialize reporter.

        Args:
            verbose: Enable detailed output
        """
        self.verbose = verbose
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging for progress reporting."""
        # Use existing logger configuration
        pass

    def info(self, message: str) -> None:
        """Log info message with REWRITE prefix."""
        logger.info(f"{self.PREFIX_REWRITE} {message}")

    def debate(self, message: str) -> None:
        """Log debate message with DEBATE prefix."""
        logger.info(f"{self.PREFIX_DEBATE} {message}")

    def judge(self, message: str) -> None:
        """Log judge message with JUDGE prefix."""
        logger.info(f"{self.PREFIX_JUDGE} {message}")

    def report_reading_files(self, source_path: Path, conclusion_path: Path) -> None:
        """Report file reading phase."""
        self.info(f"Reading source file: {source_path}")
        self.info(f"Reading conclusion: {conclusion_path}")

    def report_revisions_found(self, count: int) -> None:
        """Report number of revisions found."""
        self.info(f"Found {count} revision(s) to apply")

    def report_applying_revisions(self) -> None:
        """Report start of revision application."""
        self.info("Applying revisions...")

    def report_backup_created(self, backup_path: Optional[Path]) -> None:
        """Report backup creation."""
        if backup_path:
            self.info(f"Backup created: {backup_path}")
        else:
            self.info("No backup created (--no-backup)")

    def report_debate_starting(self, round_num: int, max_rounds: int) -> None:
        """Report start of debate round."""
        self.debate(f"Starting verification round {round_num}/{max_rounds}")

    def report_debate_complete(self, rounds: int) -> None:
        """Report debate completion."""
        self.debate(f"Verification complete after {rounds} round(s)")

    def report_pro_argument(self, summary: str) -> None:
        """Report PRO argument summary."""
        if self.verbose:
            self.debate(f"PRO: {summary}")

    def report_con_argument(self, summary: str) -> None:
        """Report CON argument summary."""
        if self.verbose:
            self.debate(f"CON: {summary}")

    def report_judge_verdict(self, verdict_summary: str) -> None:
        """Report judge verdict."""
        self.judge(verdict_summary)

    def report_verification_status(self, verified: int, total: int) -> None:
        """Report current verification status."""
        self.debate(f"Verification: {verified}/{total} revisions confirmed")

    def report_round_progress(self, round_num: int, max_rounds: int,
                             verified: int, total: int) -> None:
        """Report progress for current round."""
        self.debate(f"Round {round_num}/{max_rounds}: {verified}/{total} verified")

    def report_revisions_remaining(self, remaining: List[RevisionItem]) -> None:
        """Report remaining unverified revisions."""
        if not remaining:
            return

        self.debate(f"Remaining revisions: {len(remaining)}")
        for rev in remaining[:5]:  # Show first 5
            self.debate(f"  - {rev.id}: {rev.content[:50]}...")
        if len(remaining) > 5:
            self.debate(f"  ... and {len(remaining) - 5} more")

    def report_result(self, result: RewriteResult) -> None:
        """Report final rewrite result."""
        if result.status == RewriteStatus.SUCCESS:
            self._report_success(result)
        elif result.status == RewriteStatus.PARTIAL:
            self._report_partial(result)
        else:
            self._report_failure(result)

    def _report_success(self, result: RewriteResult) -> None:
        """Report successful completion."""
        self.info(f"✓ Complete: All {result.revisions_total} revisions verified")

    def _report_partial(self, result: RewriteResult) -> None:
        """Report partial completion."""
        self.info(f"⚠ Partial completion: {result.revisions_verified}/{result.revisions_total} verified")
        self.report_revisions_remaining(list(result.unverified))
        self._report_recommendations(result)

    def _report_failure(self, result: RewriteResult) -> None:
        """Report failure."""
        self.info(f"✗ Failed: No revisions could be applied")

    def _report_recommendations(self, result: RewriteResult) -> None:
        """Report recommendations for partial completion."""
        self.info("")
        self.info("Recommendations:")
        self.info("- Review unverified revisions above")
        self.info("- Consider running rewrite again with --max-rounds")
        self.info("- Manually apply remaining revisions if needed")
        self.info("")
