"""
Pydantic models for SDD analysis MCP tool.

Defines input/output schemas for specification analysis.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class AnalyzeSpecInput(BaseModel):
    """Input model for analyze_specification tool."""

    spec_path: Optional[str] = Field(
        default=None,
        description="Path to specification file (.md or .txt)"
    )

    spec_content: Optional[str] = Field(
        default=None,
        description="Raw specification content (text/markdown)"
    )

    spec_type: str = Field(
        default="SDD",
        description="Type of specification: PRD, SDD, TDD, or UNKNOWN"
    )

    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Optional list of focus areas for analysis"
    )

    detail_level: str = Field(
        default="thorough",
        description="Analysis detail level: 'quick' (2 rounds) or 'thorough' (4 rounds)"
    )

    config_path: Optional[str] = Field(
        default=None,
        description="Optional path to sdd_config.yaml (default: config/sdd_config.yaml)"
    )

    @field_validator('spec_type')
    @classmethod
    def validate_spec_type(cls, v: str) -> str:
        """Validate specification type."""
        valid_types = ['PRD', 'SDD', 'TDD', 'UNKNOWN']
        v_upper = v.upper()
        if v_upper not in valid_types:
            raise ValueError(f"Invalid spec_type: {v}. Must be one of {valid_types}")
        return v_upper

    @field_validator('detail_level')
    @classmethod
    def validate_detail_level(cls, v: str) -> str:
        """Validate detail level."""
        valid_levels = ['quick', 'thorough']
        v_lower = v.lower()
        if v_lower not in valid_levels:
            raise ValueError(f"Invalid detail_level: {v}. Must be one of {valid_levels}")
        return v_lower

    @field_validator('spec_path', 'spec_content')
    @classmethod
    def validate_exactly_one(cls, v, info) -> Any:
        """Validate exactly one of spec_path or spec_content is provided."""
        # This will be called for each field, so we need to check both
        # We'll do the actual validation in a separate method
        return v

    def validate_input(self) -> None:
        """Validate that exactly one of spec_path or spec_content is provided."""
        has_path = self.spec_path is not None
        has_content = self.spec_content is not None

        if not has_path and not has_content:
            raise ValueError("Either spec_path or spec_content must be provided")

        if has_path and has_content:
            raise ValueError("Only one of spec_path or spec_content should be provided, not both")


class WeakPoint(BaseModel):
    """A weak point identified in the specification."""

    section: str = Field(description="Section where weak point was found")
    severity: str = Field(description="Severity level: low, medium, high, critical")
    description: str = Field(description="Description of the weak point")
    recommendation: Optional[str] = Field(default=None, description="Suggested improvement")


class Recommendation(BaseModel):
    """A recommendation for improving the specification."""

    section: str = Field(description="Section this recommendation applies to")
    priority: str = Field(description="Priority: low, medium, high")
    action: str = Field(description="Recommended action")
    rationale: Optional[str] = Field(default=None, description="Why this recommendation is made")


class UnclearSection(BaseModel):
    """An unclear section in the specification."""

    section: str = Field(description="Section that is unclear")
    issue: str = Field(description="What is unclear about this section")
    suggested_clarification: Optional[str] = Field(default=None, description="Suggested clarification")


class AnalysisMetadata(BaseModel):
    """Metadata about the analysis process."""

    model_used: str = Field(description="LLM model used for analysis")
    agents_used: List[str] = Field(description="Agents that participated in the debate")
    analysis_time_ms: int = Field(description="Total analysis time in milliseconds")
    debate_mode: str = Field(description="Debate mode used: standard or simple")
    num_rounds: int = Field(description="Number of debate rounds")
    winner: Optional[str] = Field(default=None, description="Debate winner: PRO or CON")


class AnalysisError(BaseModel):
    """Error information for failed analysis."""

    type: str = Field(description="Error type: validation, timeout, rate_limit, auth, parsing, unknown")
    message: str = Field(description="Human-readable error message")
    recoverable: bool = Field(description="Whether the error is recoverable (retry may help)")
    suggestion: Optional[str] = Field(default=None, description="Suggested action to fix the error")


class SDDAnalysisResult(BaseModel):
    """Result of SDD specification analysis."""

    status: str = Field(description="Analysis status: success, partial, error")
    weak_points: List[WeakPoint] = Field(default_factory=list, description="Identified weak points")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Improvement recommendations")
    unclear_sections: List[UnclearSection] = Field(default_factory=list, description="Unclear sections")
    metadata: AnalysisMetadata = Field(description="Analysis metadata")
    error: Optional[AnalysisError] = Field(default=None, description="Error details if status is error")

    # For partial results
    partial_reason: Optional[str] = Field(
        default=None,
        description="Reason for partial status (e.g., timeout, rate limit)"
    )
