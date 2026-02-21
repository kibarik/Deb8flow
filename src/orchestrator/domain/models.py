"""Domain models for orchestrator configuration and state.

This module defines the core domain entities including configuration,
workflow phases, validation results, and orchestration outcomes.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class OverwriteOutputMode(str, Enum):
    """Mode for handling existing output files."""

    ERROR = "error"
    OVERWRITE = "overwrite"
    TIMESTAMP = "timestamp"


class LogLevel(str, Enum):
    """Logging level enum."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class PhaseName(str, Enum):
    """Valid Spec-Kitty workflow phase names."""

    SPECIFY = "specify"
    RESEARCH = "research"
    PLAN = "plan"
    TASKS = "tasks"
    IMPLEMENT = "implement"
    REVIEW = "review"
    ACCEPT = "accept"


class PhaseConfig(BaseModel):
    """Configuration for a single workflow phase.

    Attributes:
        name: Phase identifier (must be valid Spec-Kitty phase name)
        enabled: Whether the phase is executed
        validate_artifact: Whether to validate artifact after phase completion
        timeout: Optional phase-specific timeout in seconds
    """

    model_config = ConfigDict(use_enum_values=True)

    name: PhaseName
    enabled: bool = True
    validate_artifact: bool = False  # Renamed to avoid shadowing BaseModel.validate
    timeout: Optional[int] = None


class OrchestratorConfig(BaseModel):
    """Configuration for the orchestrator system.

    This configuration is loaded from config/debate_config.yaml under
    the orchestrator: section. All fields have sensible defaults
    and are validated on load.

    Attributes:
        max_retries: Maximum retry attempts per phase when validation fails
        validation_timeout: Seconds to wait for artifact validation
        auto_accept: Skip final acceptance prompt (fully automated mode)
        keep_containers: Don't stop containers after completion (for debugging)
        output_suffix: Suffix to append to corrected output files
        timestamp_output: Add timestamp to output filename
        overwrite_output: Behavior when output file already exists
        docker_image: Docker image to use for Claude Code environment
        container_timeout: Maximum time before container is force-stopped
        container_memory_limit: Container memory limit (e.g., "2g", "512m")
        container_cpu_quota: Container CPU quota (1.0 = 1 CPU)
        log_dir: Directory for orchestrator log files
        log_level: Logging level
        verbose: Enable verbose console output
        claude_cli_path: Optional path to Claude Code CLI binary
        phases: Phase-specific configuration list
    """

    model_config = ConfigDict(use_enum_values=True)

    # Workflow control
    max_retries: int = Field(default=3, ge=0, le=10)
    validation_timeout: int = Field(default=30, ge=5, le=300)
    auto_accept: bool = False

    # Output settings
    output_suffix: str = Field(default=".corrected.", pattern=r"^[a-z.]+$")
    timestamp_output: bool = False
    overwrite_output: OverwriteOutputMode = OverwriteOutputMode.ERROR

    # Container management
    keep_containers: bool = False
    docker_image: str = "claude-code:latest"
    container_timeout: int = Field(default=3600, ge=60, le=86400)
    container_memory_limit: Optional[str] = "2g"
    container_cpu_quota: Optional[float] = Field(default=1.0, gt=0, le=8.0)

    # Logging
    log_dir: str = ".orchestrator/logs"
    log_level: LogLevel = LogLevel.INFO
    verbose: bool = False

    # Claude Code CLI
    claude_cli_path: Optional[str] = None

    # Phase configuration
    phases: List[PhaseConfig] = Field(default_factory=list)

    @field_validator("phases")
    @classmethod
    def validate_unique_phase_names(cls, v: List[PhaseConfig]) -> List[PhaseConfig]:
        """Ensure phase names are unique."""
        names = [phase.name for phase in v]
        if len(names) != len(set(names)):
            raise ValueError("Phase names must be unique")
        return v

    @model_validator(mode="after")
    def populate_default_phases(self) -> "OrchestratorConfig":
        """Populate default phases if list is empty."""
        if not self.phases:
            self.phases = self._get_default_phases()
        return self

    @model_validator(mode="after")
    def validate_phase_names(self) -> "OrchestratorConfig":
        """Ensure all phase names are valid Spec-Kitty phases."""
        valid_phases = {p.value for p in PhaseName}
        for phase in self.phases:
            if phase.name not in valid_phases:
                raise ValueError(
                    f"Invalid phase name: {phase.name}. "
                    f"Must be one of: {', '.join(valid_phases)}"
                )
        return self

    @staticmethod
    def _get_default_phases() -> List[PhaseConfig]:
        """Get default phase configuration.

        Returns all 7 Spec-Kitty phases with appropriate defaults.
        Validation enabled for: specify, plan, tasks, implement
        """
        return [
            PhaseConfig(name=PhaseName.SPECIFY, enabled=True, validate_artifact=True),
            PhaseConfig(name=PhaseName.RESEARCH, enabled=True, validate_artifact=False),
            PhaseConfig(name=PhaseName.PLAN, enabled=True, validate_artifact=True),
            PhaseConfig(name=PhaseName.TASKS, enabled=True, validate_artifact=True),
            PhaseConfig(name=PhaseName.IMPLEMENT, enabled=True, validate_artifact=True),
            PhaseConfig(name=PhaseName.REVIEW, enabled=True, validate_artifact=False),
            PhaseConfig(name=PhaseName.ACCEPT, enabled=True, validate_artifact=False),
        ]

    def is_valid(self) -> bool:
        """Check if all validations pass."""
        # Pydantic v2 validates on construction, so if we're here,
        # the model is valid unless there are custom validation issues
        return True

    @property
    def errors(self) -> List[str]:
        """Return list of validation errors."""
        return []  # Pydantic v2 validates on construction


class ResultStatus(str, Enum):
    """Overall execution status."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class OrchestratorResult(BaseModel):
    """Result of orchestrator execution.

    Aggregates results from all workflow phases into a single outcome.

    Attributes:
        status: Overall execution status
        phases_completed: Number of phases successfully completed
        total_phases: Total number of phases configured
        total_retries: Total retry attempts across all phases
        duration_seconds: Total execution time
        output_path: Path to corrected output file (if any)
        failed_phase: Name of phase that failed (if any)
        container_id: Docker container ID for debugging
        error_summary: List of errors encountered
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: ResultStatus
    phases_completed: int = 0
    total_phases: int = 0
    total_retries: int = 0
    duration_seconds: int = 0
    output_path: Optional[Path] = None
    failed_phase: Optional[str] = None
    container_id: Optional[str] = None
    error_summary: List[str] = Field(default_factory=list)

    @classmethod
    def from_phases(cls, phases: list) -> "OrchestratorResult":
        """Aggregate results from workflow phases.

        Args:
            phases: List of WorkflowPhase instances

        Returns:
            OrchestratorResult with aggregated data
        """
        from src.orchestrator.domain.phase import PhaseStatus

        completed_count = sum(1 for p in phases if p.status == PhaseStatus.COMPLETED)
        total_retries = sum(p.attempts - 1 for p in phases)  # Subtract first attempt

        # Determine overall status
        failed_phase = None
        error_messages = []

        for p in phases:
            if p.status == PhaseStatus.FAILED and failed_phase is None:
                failed_phase = p.name
            if p.error_message:
                error_messages.append(f"{p.name}: {p.error_message}")

        if failed_phase:
            status = ResultStatus.FAILED if completed_count == 0 else ResultStatus.PARTIAL
        elif completed_count == len(phases):
            status = ResultStatus.SUCCESS
        else:
            status = ResultStatus.PARTIAL

        # Calculate duration
        start_times = [p.started_at for p in phases if p.started_at]
        end_times = [p.completed_at for p in phases if p.completed_at]

        duration = 0
        if start_times and end_times:
            duration = int((max(end_times) - min(start_times)).total_seconds())

        return cls(
            status=status,
            phases_completed=completed_count,
            total_phases=len(phases),
            total_retries=total_retries,
            duration_seconds=duration,
            failed_phase=failed_phase,
            error_summary=error_messages,
        )


class ArtifactMetadata(BaseModel):
    """Metadata extracted from Spec-Kitty artifacts.

    Attributes:
        artifact_type: Type of artifact (spec, plan, tasks)
        path: Path to artifact file
        frontmatter: YAML frontmatter content
        mandatory_sections: List of mandatory section names
        present_sections: List of present section names
        clarifications_needed: Count of [NEEDS CLARIFICATION] markers
        is_complete: Whether artifact is complete
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    artifact_type: str
    path: Path
    frontmatter: dict = Field(default_factory=dict)
    mandatory_sections: List[str] = Field(default_factory=list)
    present_sections: List[str] = Field(default_factory=list)
    clarifications_needed: int = 0
    is_complete: bool = False

    @classmethod
    def from_markdown(cls, path: Path) -> "ArtifactMetadata":
        """Extract metadata from a markdown artifact file.

        Parses YAML frontmatter and section headers to determine
        artifact completeness.

        Args:
            path: Path to the artifact file

        Returns:
            ArtifactMetadata with extracted information
        """
        import re
        import yaml

        content = path.read_text()

        # Parse frontmatter
        frontmatter = {}
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if frontmatter_match:
            try:
                frontmatter = yaml.safe_load(frontmatter_match.group(1)) or {}
            except yaml.YAMLError:
                pass

        # Extract section headers
        sections = re.findall(r"^## (.+)$", content, re.MULTILINE)

        # Count clarification markers
        clarifications = content.count("[NEEDS CLARIFICATION")

        # Determine artifact type from path
        artifact_type = "unknown"
        if "spec.md" in str(path):
            artifact_type = "spec"
        elif "plan.md" in str(path):
            artifact_type = "plan"
        elif "tasks.md" in str(path):
            artifact_type = "tasks"

        # Define mandatory sections per type
        mandatory_sections_map = {
            "spec": ["Overview", "Requirements", "Success Criteria"],
            "plan": ["Technical Context", "Project Structure", "Phase Gates"],
            "tasks": ["Work Package"],
        }
        mandatory_sections = mandatory_sections_map.get(artifact_type, [])

        # Check completeness
        is_complete = (
            clarifications == 0
            and all(s in sections for s in mandatory_sections)
        )

        return cls(
            artifact_type=artifact_type,
            path=path,
            frontmatter=frontmatter,
            mandatory_sections=mandatory_sections,
            present_sections=sections,
            clarifications_needed=clarifications,
            is_complete=is_complete,
        )
