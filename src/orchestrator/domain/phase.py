"""Workflow phase domain model with thread-safe state transitions.

This module defines the WorkflowPhase entity that tracks the state of
individual Spec-Kitty workflow phases with thread-safe transitions.
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class PhaseStatus(str, Enum):
    """Status of a workflow phase.

    Transitions:
        pending → running → (completed | failed | retrying)
        retrying → running
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class ValidationStatus(str, Enum):
    """Result of artifact validation.

    PASSED: Artifact validated successfully
    FAILED: Artifact validation failed
    SKIPPED: Validation not configured for this phase
    """

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, current_status: PhaseStatus, target_status: PhaseStatus):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Invalid state transition: {current_status.value} → {target_status.value}"
        )


# Valid state transitions
_VALID_TRANSITIONS = {
    PhaseStatus.PENDING: {PhaseStatus.RUNNING},
    PhaseStatus.RUNNING: {
        PhaseStatus.COMPLETED,
        PhaseStatus.FAILED,
        PhaseStatus.RETRYING,
    },
    PhaseStatus.RETRYING: {PhaseStatus.RUNNING},
    # Terminal states: no transitions allowed
    PhaseStatus.COMPLETED: set(),
    PhaseStatus.FAILED: set(),
}


@dataclass
class WorkflowPhase:
    """Represents the state of a single workflow phase.

    This class tracks phase execution state with thread-safe transitions.
    Mutable fields are protected by RLock to ensure safe concurrent access.

    Attributes:
        name: Phase identifier (e.g., "specify", "plan")
        status: Current phase status (protected by lock)
        attempts: Number of execution attempts (protected by lock)
        artifact_path: Path to generated artifact (if any) - immutable
        validation_result: Result of artifact validation - immutable
        started_at: When phase execution started (protected by lock)
        completed_at: When phase execution completed (protected by lock)
        error_message: Error message if failed (protected by lock)
    """

    name: str
    artifact_path: Optional[Path] = None
    validation_result: Optional[ValidationStatus] = None

    # Thread-protected mutable fields
    _status: PhaseStatus = field(default=PhaseStatus.PENDING, init=False)
    _attempts: int = field(default=0, init=False)
    _started_at: Optional[datetime] = field(default=None, init=False)
    _completed_at: Optional[datetime] = field(default=None, init=False)
    _error_message: Optional[str] = field(default=None, init=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False)

    def __post_init__(self):
        """Initialize the phase after creation."""
        # Validate name is a string
        if not isinstance(self.name, str):
            raise TypeError(f"name must be a string, got {type(self.name)}")

    @property
    def status(self) -> PhaseStatus:
        """Get current phase status (thread-safe)."""
        with self._lock:
            return self._status

    @status.setter
    def status(self, value: PhaseStatus):
        """Set phase status with validation (thread-safe)."""
        with self._lock:
            if not self.can_transition_to(value):
                raise InvalidStateTransitionError(self._status, value)
            self._status = value

    @property
    def attempts(self) -> int:
        """Get number of execution attempts (thread-safe)."""
        with self._lock:
            return self._attempts

    @property
    def started_at(self) -> Optional[datetime]:
        """Get phase start time (thread-safe)."""
        with self._lock:
            return self._started_at

    @property
    def completed_at(self) -> Optional[datetime]:
        """Get phase completion time (thread-safe)."""
        with self._lock:
            return self._completed_at

    @property
    def error_message(self) -> Optional[str]:
        """Get error message if phase failed (thread-safe)."""
        with self._lock:
            return self._error_message

    def can_transition_to(self, target_status: PhaseStatus) -> bool:
        """Check if transition to target status is valid.

        Args:
            target_status: Desired target status

        Returns:
            True if transition is valid, False otherwise
        """
        with self._lock:
            return target_status in _VALID_TRANSITIONS.get(self._status, set())

    def transition_to(self, target_status: PhaseStatus) -> None:
        """Transition to target status with timestamp updates.

        Updates timestamps automatically:
        - PENDING → RUNNING: sets started_at
        - RUNNING → COMPLETED/FAILED: sets completed_at
        - RUNNING → RETRYING: no timestamp change

        Args:
            target_status: Desired target status

        Raises:
            InvalidStateTransitionError: If transition is invalid
        """
        with self._lock:
            if not self.can_transition_to(target_status):
                raise InvalidStateTransitionError(self._status, target_status)

            # Update timestamps on transitions
            if target_status == PhaseStatus.RUNNING:
                if self._attempts == 0:
                    self._started_at = datetime.now()
                self._attempts += 1

            if target_status in (PhaseStatus.COMPLETED, PhaseStatus.FAILED):
                self._completed_at = datetime.now()

            self._status = target_status

    def increment_attempts(self) -> int:
        """Increment attempt counter and return new value.

        Returns:
            New attempt count
        """
        with self._lock:
            self._attempts += 1
            return self._attempts

    def set_error(self, message: str) -> None:
        """Set error message and transition to failed status.

        Args:
            message: Error message to store
        """
        with self._lock:
            self._error_message = message
            self._status = PhaseStatus.FAILED
            self._completed_at = datetime.now()

    def set_validation_result(self, result: ValidationStatus) -> None:
        """Set validation result.

        Args:
            result: Validation result
        """
        # validation_result is immutable after set, no lock needed for write
        # But we set it as a new attribute since dataclass is frozen-ish
        object.__setattr__(self, "validation_result", result)

    def is_terminal(self) -> bool:
        """Check if phase is in a terminal state.

        Returns:
            True if phase is completed or failed
        """
        return self.status in (PhaseStatus.COMPLETED, PhaseStatus.FAILED)

    def __repr__(self) -> str:
        """String representation of phase state."""
        return (
            f"WorkflowPhase(name={self.name!r}, status={self.status.value}, "
            f"attempts={self.attempts})"
        )
