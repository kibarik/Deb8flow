"""Unit tests for workflow phase state machine and thread safety."""

import threading
import time
from pathlib import Path

import pytest

from src.orchestrator.domain.phase import (
    InvalidStateTransitionError,
    PhaseStatus,
    ValidationStatus,
    WorkflowPhase,
)
from src.orchestrator.domain.models import (
    ArtifactMetadata,
    OrchestratorResult,
    ResultStatus,
)


class TestPhaseStatusEnum:
    """Tests for PhaseStatus enum values."""

    def test_all_enum_values_defined(self):
        """Test that all required enum values are defined."""
        expected_values = {
            "pending",
            "running",
            "completed",
            "failed",
            "retrying",
        }
        actual_values = {status.value for status in PhaseStatus}
        assert actual_values == expected_values


class TestValidationStatusEnum:
    """Tests for ValidationStatus enum values."""

    def test_all_enum_values_defined(self):
        """Test that all required enum values are defined."""
        expected_values = {"passed", "failed", "skipped"}
        actual_values = {status.value for status in ValidationStatus}
        assert actual_values == expected_values


class TestValidTransitions:
    """Tests for valid state transitions."""

    def test_pending_to_running(self):
        """Test pending → running transition."""
        phase = WorkflowPhase(name="specify")
        assert phase.status == PhaseStatus.PENDING

        phase.transition_to(PhaseStatus.RUNNING)
        assert phase.status == PhaseStatus.RUNNING
        assert phase.attempts == 1
        assert phase.started_at is not None

    def test_running_to_completed(self):
        """Test running → completed transition."""
        phase = WorkflowPhase(name="specify")
        phase.transition_to(PhaseStatus.RUNNING)

        phase.transition_to(PhaseStatus.COMPLETED)
        assert phase.status == PhaseStatus.COMPLETED
        assert phase.completed_at is not None

    def test_running_to_failed(self):
        """Test running → failed transition."""
        phase = WorkflowPhase(name="specify")
        phase.transition_to(PhaseStatus.RUNNING)

        phase.transition_to(PhaseStatus.FAILED)
        assert phase.status == PhaseStatus.FAILED
        assert phase.completed_at is not None

    def test_running_to_retrying(self):
        """Test running → retrying transition."""
        phase = WorkflowPhase(name="specify")
        phase.transition_to(PhaseStatus.RUNNING)

        phase.transition_to(PhaseStatus.RETRYING)
        assert phase.status == PhaseStatus.RETRYING

    def test_retrying_to_running(self):
        """Test retrying → running transition."""
        phase = WorkflowPhase(name="specify")
        phase.transition_to(PhaseStatus.RUNNING)
        phase.transition_to(PhaseStatus.RETRYING)

        phase.transition_to(PhaseStatus.RUNNING)
        assert phase.status == PhaseStatus.RUNNING
        assert phase.attempts == 2  # Incremented on second transition to running


class TestInvalidTransitions:
    """Tests for invalid state transitions."""

    def test_invalid_transition_raises_error(self):
        """Test that invalid transitions raise InvalidStateTransitionError."""
        phase = WorkflowPhase(name="specify")

        with pytest.raises(InvalidStateTransitionError):
            phase.transition_to(PhaseStatus.COMPLETED)  # Can't skip RUNNING

    def test_completed_to_running_raises_error(self):
        """Test that completed → running is invalid."""
        phase = WorkflowPhase(name="specify")
        phase.transition_to(PhaseStatus.RUNNING)
        phase.transition_to(PhaseStatus.COMPLETED)

        with pytest.raises(InvalidStateTransitionError):
            phase.transition_to(PhaseStatus.RUNNING)

    def test_failed_to_running_raises_error(self):
        """Test that failed → running is invalid."""
        phase = WorkflowPhase(name="specify")
        phase.transition_to(PhaseStatus.RUNNING)
        phase.transition_to(PhaseStatus.FAILED)

        with pytest.raises(InvalidStateTransitionError):
            phase.transition_to(PhaseStatus.RUNNING)

    def test_can_transition_to_method(self):
        """Test can_transition_to() method."""
        phase = WorkflowPhase(name="specify")

        assert phase.can_transition_to(PhaseStatus.RUNNING) is True
        assert phase.can_transition_to(PhaseStatus.COMPLETED) is False

        phase.transition_to(PhaseStatus.RUNNING)
        assert phase.can_transition_to(PhaseStatus.COMPLETED) is True
        assert phase.can_transition_to(PhaseStatus.PENDING) is False


class TestThreadSafeStateUpdates:
    """Tests for thread-safe state updates."""

    def test_concurrent_status_reads(self):
        """Test that concurrent reads are thread-safe."""
        phase = WorkflowPhase(name="specify")
        phase.transition_to(PhaseStatus.RUNNING)

        results = []

        def read_status():
            for _ in range(100):
                results.append(phase.status)

        threads = [threading.Thread(target=read_status) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(r == PhaseStatus.RUNNING for r in results)

    def test_concurrent_transitions(self):
        """Test that concurrent transitions are handled safely."""
        phase = WorkflowPhase(name="specify")
        errors = []

        def try_transition():
            try:
                phase.transition_to(PhaseStatus.RUNNING)
            except InvalidStateTransitionError:
                errors.append("transition_error")

        threads = [threading.Thread(target=try_transition) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Only one thread should succeed in transitioning
        assert phase.status == PhaseStatus.RUNNING
        assert phase.attempts == 1

    def test_increment_attempts_thread_safety(self):
        """Test that increment_attempts is thread-safe."""
        phase = WorkflowPhase(name="specify")

        def increment():
            for _ in range(100):
                phase.increment_attempts()

        threads = [threading.Thread(target=increment) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert phase.attempts == 1000


class TestWorkflowPhaseProperties:
    """Tests for WorkflowPhase properties and methods."""

    def test_set_error_transitions_to_failed(self):
        """Test that set_error() transitions to failed and sets message."""
        phase = WorkflowPhase(name="specify")
        phase.transition_to(PhaseStatus.RUNNING)

        phase.set_error("Something went wrong")

        assert phase.status == PhaseStatus.FAILED
        assert phase.error_message == "Something went wrong"
        assert phase.completed_at is not None

    def test_set_validation_result(self):
        """Test setting validation result."""
        phase = WorkflowPhase(name="specify")

        phase.set_validation_result(ValidationStatus.PASSED)
        assert phase.validation_result == ValidationStatus.PASSED

        phase.set_validation_result(ValidationStatus.FAILED)
        assert phase.validation_result == ValidationStatus.FAILED

    def test_is_terminal(self):
        """Test is_terminal() method."""
        phase = WorkflowPhase(name="specify")

        assert phase.is_terminal() is False

        phase.transition_to(PhaseStatus.RUNNING)
        assert phase.is_terminal() is False

        phase.transition_to(PhaseStatus.COMPLETED)
        assert phase.is_terminal() is True


class TestOrchestratorResultAggregation:
    """Tests for OrchestratorResult.from_phases() method."""

    def test_all_phases_completed(self):
        """Test aggregation when all phases complete."""
        phases = [
            WorkflowPhase(name="specify"),
            WorkflowPhase(name="plan"),
            WorkflowPhase(name="tasks"),
        ]

        for p in phases:
            p.transition_to(PhaseStatus.RUNNING)
            p.transition_to(PhaseStatus.COMPLETED)

        result = OrchestratorResult.from_phases(phases)

        assert result.status == ResultStatus.SUCCESS
        assert result.phases_completed == 3
        assert result.total_phases == 3
        assert result.total_retries == 0
        assert result.failed_phase is None

    def test_one_phase_failed(self):
        """Test aggregation when one phase fails."""
        phases = [
            WorkflowPhase(name="specify"),
            WorkflowPhase(name="plan"),
            WorkflowPhase(name="tasks"),
        ]

        phases[0].transition_to(PhaseStatus.RUNNING)
        phases[0].transition_to(PhaseStatus.COMPLETED)

        phases[1].transition_to(PhaseStatus.RUNNING)
        phases[1].set_error("Plan failed")

        phases[2].transition_to(PhaseStatus.RUNNING)
        phases[2].transition_to(PhaseStatus.COMPLETED)

        result = OrchestratorResult.from_phases(phases)

        assert result.status == ResultStatus.PARTIAL
        assert result.phases_completed == 2
        assert result.failed_phase == "plan"
        assert "plan: Plan failed" in result.error_summary

    def test_all_phases_failed(self):
        """Test aggregation when all phases fail."""
        phases = [
            WorkflowPhase(name="specify"),
            WorkflowPhase(name="plan"),
        ]

        for p in phases:
            p.transition_to(PhaseStatus.RUNNING)
            p.set_error("Failed")

        result = OrchestratorResult.from_phases(phases)

        assert result.status == ResultStatus.FAILED
        assert result.phases_completed == 0

    def test_retry_counting(self):
        """Test that retries are counted correctly."""
        phases = [WorkflowPhase(name="specify")]

        phases[0].transition_to(PhaseStatus.RUNNING)
        phases[0].transition_to(PhaseStatus.RETRYING)
        phases[0].transition_to(PhaseStatus.RUNNING)
        phases[0].transition_to(PhaseStatus.RETRYING)
        phases[0].transition_to(PhaseStatus.RUNNING)
        phases[0].transition_to(PhaseStatus.COMPLETED)

        result = OrchestratorResult.from_phases(phases)

        assert result.total_retries == 2  # 3 attempts - 1 initial

    def test_duration_calculation(self):
        """Test that duration is calculated correctly."""
        import time

        phases = [WorkflowPhase(name="specify")]

        phases[0].transition_to(PhaseStatus.RUNNING)
        time.sleep(0.01)  # Small delay
        phases[0].transition_to(PhaseStatus.COMPLETED)

        result = OrchestratorResult.from_phases(phases)

        assert result.duration_seconds >= 0


class TestArtifactMetadata:
    """Tests for ArtifactMetadata parsing."""

    def test_parse_valid_spec(self, tmp_path):
        """Test parsing a valid spec.md file."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("""
---
feature_number: "021"
slug: "test-feature"
---

## Overview
Test feature overview.

## Requirements
Functional requirements.

## Success Criteria
Definition of success.
""")

        metadata = ArtifactMetadata.from_markdown(spec_file)

        assert metadata.artifact_type == "spec"
        assert metadata.is_complete is True
        assert metadata.clarifications_needed == 0

    def test_detect_incomplete_artifact(self, tmp_path):
        """Test detection of incomplete artifact."""
        spec_file = tmp_path / "spec.md"
        spec_file.write_text("""
---
feature_number: "021"
---

## Overview
Missing sections.

[NEEDS CLARIFICATION: What sections?]
""")

        metadata = ArtifactMetadata.from_markdown(spec_file)

        assert metadata.is_complete is False
        assert metadata.clarifications_needed == 1
