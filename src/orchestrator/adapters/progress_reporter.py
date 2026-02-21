"""Progress reporter for orchestrator console output.

This module provides formatted console output for workflow progress
with [ORCHESTRATOR] prefix.
"""

import logging
import sys
from datetime import timedelta
from typing import Optional

from src.orchestrator.domain.models import OrchestratorResult, ResultStatus

logger = logging.getLogger(__name__)

# ANSI color codes for terminal output
class Colors:
    """ANSI color codes."""
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def format_duration(seconds: int) -> str:
    """Format duration in seconds as human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "1m 23s")
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


class ProgressReporter:
    """Reporter for workflow progress and results.

    Provides formatted console output with [ORCHESTRATOR] prefix.
    Respects verbose flag for additional detail.
    """

    def __init__(self, verbose: bool = False):
        """Initialize progress reporter.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self._phase_count = 0
        self._total_phases = 0

    def set_total_phases(self, total: int) -> None:
        """Set total number of phases for progress tracking.

        Args:
            total: Total number of phases
        """
        self._total_phases = total

    def phase_start(self, name: str, command: Optional[str] = None) -> None:
        """Report phase start.

        Args:
            name: Phase name
            command: Optional command being executed
        """
        self._phase_count += 1
        cmd_str = f" → {command}" if command and self.verbose else ""
        print(f"[ORCHESTRATOR] Phase: {name} → Running{cmd_str}")

    def phase_complete(
        self,
        name: str,
        attempts: int = 1,
        validated: bool = False,
    ) -> None:
        """Report successful phase completion.

        Args:
            name: Phase name
            attempts: Number of attempts taken
            validated: Whether validation was performed
        """
        status = "Validation passed" if validated else "Completed"
        attempts_str = f" ({attempts} attempt{'s' if attempts > 1 else ''})" if attempts > 1 else ""
        print(f"[ORCHESTRATOR] {Colors.GREEN}Phase: {name} → {status}{attempts_str}{Colors.RESET}")

    def phase_error(self, name: str, message: str) -> None:
        """Report phase error.

        Args:
            name: Phase name
            message: Error message
        """
        print(f"[ORCHESTRATOR] {Colors.RED}Phase: {name} → ERROR: {message}{Colors.RESET}")

    def phase_retrying(self, name: str, attempt: int, max_attempts: int) -> None:
        """Report phase retry.

        Args:
            name: Phase name
            attempt: Current attempt number
            max_attempts: Maximum number of attempts
        """
        print(f"[ORCHESTRATOR] {Colors.YELLOW}Phase: {name} → Retrying ({attempt}/{max_attempts}){Colors.RESET}")

    def summary(self, result: OrchestratorResult) -> None:
        """Report final workflow summary.

        Args:
            result: Orchestrator result with aggregated data
        """
        status_color = {
            ResultStatus.SUCCESS: Colors.GREEN,
            ResultStatus.PARTIAL: Colors.YELLOW,
            ResultStatus.FAILED: Colors.RED,
        }.get(result.status, "")

        status_str = f"{status_color}{result.status.value.upper()}{Colors.RESET}"

        print(f"\n[ORCHESTRATOR] {Colors.BOLD}Workflow Complete: {status_str}{Colors.RESET}")
        print(f"[ORCHESTRATOR] Phases: {result.phases_completed}/{result.total_phases} successful")

        if result.total_retries > 0:
            print(f"[ORCHESTRATOR] Retries: {result.total_retries} total")

        if result.duration_seconds > 0:
            duration_str = format_duration(result.duration_seconds)
            print(f"[ORCHESTRATOR] Duration: {duration_str}")

        if result.status == ResultStatus.SUCCESS and result.output_path:
            print(f"[ORCHESTRATOR] {Colors.GREEN}Output: {result.output_path}{Colors.RESET}")

        if result.failed_phase:
            print(f"[ORCHESTRATOR] {Colors.RED}Failed phase: {result.failed_phase}{Colors.RESET}")

        if result.error_summary:
            print(f"[ORCHESTRATOR] Errors:")
            for error in result.error_summary:
                print(f"  - {error}")

        # Exit with appropriate code
        exit_codes = {
            ResultStatus.SUCCESS: 0,
            ResultStatus.PARTIAL: 1,
            ResultStatus.FAILED: 2,
        }
        sys.exit(exit_codes.get(result.status, 2))

    def shutdown_interrupted(self, completed: int, total: int) -> None:
        """Report shutdown due to user interrupt.

        Args:
            completed: Number of phases completed
            total: Total number of phases
        """
        print(f"\n[ORCHESTRATOR] {Colors.YELLOW}Workflow interrupted by user{Colors.RESET}")
        print(f"[ORCHESTRATOR] Progress: {completed}/{total} phases completed")
        print(f"[ORCHESTRATOR] Partial results may be available in output directory")
        sys.exit(130)  # Standard exit code for SIGINT

    def info(self, message: str) -> None:
        """Report informational message.

        Args:
            message: Message to display
        """
        if self.verbose:
            print(f"[ORCHESTRATOR] {message}")

    def warning(self, message: str) -> None:
        """Report warning message.

        Args:
            message: Message to display
        """
        print(f"[ORCHESTRATOR] {Colors.YELLOW}WARNING: {message}{Colors.RESET}")

    def error(self, message: str) -> None:
        """Report error message.

        Args:
            message: Message to display
        """
        print(f"[ORCHESTRATOR] {Colors.RED}ERROR: {message}{Colors.RESET}")
