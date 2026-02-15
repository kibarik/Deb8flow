"""
Enhanced Conclusion Types for Committee Debates.

This module provides Pydantic models for the enhanced conclusion report feature,
which transforms committee debate outputs into actionable product improvement plans.

Compliance:
- FR-031: Evidence references with room_id, speaker_role, turn_index, quote (max 200 chars)
- FR-030: Length limits for 60-second readability
- FR-029: Confidence level calculation (High/Medium/Low)

Example:
    >>> from src.types.enhanced_conclusion_types import EnhancedConclusion
    >>> conclusion = EnhancedConclusion(
    ...     verdict=verdict,
    ...     role_analyses=role_analyses,
    ...     critical_gaps=gaps,
    ...     recommendations=recommendations
    ... )
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Literal


__all__ = [
    "EvidenceReference",
    "Strength",
    "Weakness",
    "RoleAnalysis",
    "Verdict",
    "IntermediateConclusionSchema",
    "CriticalGap",
    "Recommendation",
    "EnhancedConclusion",
]


# ============================================================================
# Evidence Reference (FR-031 Compliance)
# ============================================================================


class EvidenceReference(BaseModel):
    """Traceable reference to specific debate content.

    Complies with FR-031: All evidence references must include room_id,
    speaker_role, turn_index, and supporting quote (max 200 characters).

    Attributes:
        room_id: Room identifier (e.g., 'TPM_vs_CPO', 'TPM_vs_CFO')
        speaker_role: Speaker who made the statement (TPM, CPO, CFO, CTO, BDM, PRO, CON, Judge)
        turn_index: Turn number in the debate (non-negative integer)
        quote: Supporting quote, auto-truncated to max 200 characters

    Example:
        >>> evidence = EvidenceReference(
        ...     room_id="TPM_vs_CPO",
        ...     speaker_role="CPO",
        ...     turn_index=3,
        ...     quote="The platform introduces significant risk..."
        ... )
    """

    room_id: str = Field(..., description="Room identifier (e.g., 'TPM_vs_CPO')")
    speaker_role: str = Field(..., description="Speaker who made the statement")
    turn_index: int = Field(..., ge=0, description="Turn number in the debate")
    quote: str = Field(..., description="Supporting quote (auto-truncated to max 200 chars)")

    @field_validator('quote')
    @classmethod
    def truncate_quote(cls, v: str) -> str:
        """Truncate quote to max 200 characters.

        Auto-truncation is preferred over raising an error for better UX.
        """
        return v[:200] if len(v) > 200 else v


# ============================================================================
# Role-Based Analysis (FR-030 Compliance)
# ============================================================================


class Strength(BaseModel):
    """A strong argument or point made by a role.

    Attributes:
        description: What was strong (10-500 characters)
        evidence: Source of this strength with complete evidence reference

    Example:
        >>> strength = Strength(
        ...     description="Clear articulation of market opportunity",
        ...     evidence=evidence_ref
        ... )
    """

    description: str = Field(..., min_length=10, max_length=500, description="What was strong")
    evidence: EvidenceReference = Field(..., description="Source of this strength")


class Weakness(BaseModel):
    """A weakness or criticism identified by a role.

    Attributes:
        description: What was weak (10-500 characters)
        evidence: Source of this weakness with complete evidence reference

    Example:
        >>> weakness = Weakness(
        ...     description="Insufficient data on unit economics",
        ...     evidence=evidence_ref
        ... )
    """

    description: str = Field(..., min_length=10, max_length=500, description="What was weak")
    evidence: EvidenceReference = Field(..., description="Source of this weakness")


class RoleAnalysis(BaseModel):
    """Complete analysis of a single role's perspective.

    Enforces FR-030 length limit: 3-5 bullets max for strengths/weaknesses
    to ensure 60-second readability.

    Attributes:
        role_name: Role name (e.g., 'TPM', 'CPO', 'CFO', 'CTO', 'BDM')
        strengths: Strong points (0-5 items, empty list allowed)
        weaknesses: Weak points (0-5 items, empty list allowed)

    Example:
        >>> analysis = RoleAnalysis(
        ...     role_name="TPM",
        ...     strengths=[strength1, strength2, strength3],
        ...     weaknesses=[weakness1, weakness2]
        ... )
    """

    role_name: str = Field(..., description="Role name (e.g., 'TPM', 'CPO')")
    strengths: List[Strength] = Field(default_factory=list, description="Strong points (3-5 max)")
    weaknesses: List[Weakness] = Field(default_factory=list, description="Weak points (3-5 max)")

    @field_validator('strengths', 'weaknesses')
    @classmethod
    def validate_length(cls, v: list) -> list:
        """Enforce 3-5 bullet limit per FR-030."""
        if len(v) > 5:
            raise ValueError(f"Maximum 5 items allowed, got {len(v)}")
        return v


# ============================================================================
# Verdict & Intermediate Schema (FR-029, FR-030 Compliance)
# ============================================================================


class Verdict(BaseModel):
    """Clear verdict answering the user's question with confidence level.

    Complies with FR-029: Confidence calculated from room outcomes
    Complies with FR-030: Answer limited to 120-150 words for 60-second readability

    Attributes:
        answer: Direct answer to user's question (120-150 words enforced)
        confidence: Confidence level per FR-029 formula (High/Medium/Low)
        rationale: 2-3 sentence explanation of the verdict (50-500 characters)
        room_outcomes: Summary of outcomes across rooms (e.g., "Opponents won 3/4 rooms")

    Example:
        >>> verdict = Verdict(
        ...     answer="The proposal should be approved with conditions...",
        ...     confidence="Medium",
        ...     rationale="Split decision with 3-1 outcome...",
        ...     room_outcomes="Opponents won 3/4 rooms (TPM won only vs CTO)"
        ... )
    """

    answer: str = Field(..., min_length=20, max_length=1000, description="Direct answer")
    confidence: Literal["High", "Medium", "Low"] = Field(
        ..., description="Confidence level per FR-029"
    )
    rationale: str = Field(..., min_length=50, max_length=500, description="2-3 sentence explanation")
    room_outcomes: str = Field(..., description="Summary of outcomes across rooms")

    @field_validator('answer')
    @classmethod
    def validate_word_count(cls, v: str) -> str:
        """Enforce 120-150 word limit per FR-030.

        Uses simple whitespace splitting for word counting.
        This is acceptable for MVP and works for most languages including Russian.
        """
        word_count = len(v.split())
        if word_count < 120 or word_count > 150:
            raise ValueError(f"Answer must be 120-150 words, got {word_count}")
        return v


class IntermediateConclusionSchema(BaseModel):
    """Structured schema after Stage 1 extraction.

    This is the output of Stage 1 (VerdictExtractor + RoleAnalyzer)
    and input to Stage 2 (GapRecommendationGenerator).

    Attributes:
        verdict: Verdict with confidence level
        role_analyses: List of per-role analyses (at least 1 required, no duplicates)

    Example:
        >>> schema = IntermediateConclusionSchema(
        ...     verdict=verdict,
        ...     role_analyses=[tpm_analysis, cpo_analysis]
        ... )
    """

    verdict: Verdict = Field(..., description="Verdict with confidence")
    role_analyses: List[RoleAnalysis] = Field(..., min_length=1, description="Per-role analyses")

    @field_validator('role_analyses')
    @classmethod
    def validate_unique_roles(cls, v: list) -> list:
        """Ensure no duplicate role names."""
        role_names = [r.role_name for r in v]
        if len(role_names) != len(set(role_names)):
            raise ValueError("Duplicate role names detected")
        return v


# ============================================================================
# Stage 2 Output: Gaps & Recommendations
# ============================================================================


class CriticalGap(BaseModel):
    """A critical gap identified across debate participants.

    Represents a significant weakness or risk identified by multiple roles.

    Attributes:
        title: Gap title (5-100 characters)
        severity: Gap severity level (High/Medium/Low)
        description: Detailed description of the gap (20-500 characters)
        sources: Which roles raised this gap (at least 1 role name required)
        evidence: Supporting evidence references (at least 1 required)

    Example:
        >>> gap = CriticalGap(
        ...     title="Missing Unit Economics Analysis",
        ...     severity="High",
        ...     description="No detailed breakdown of CAC and LTV...",
        ...     sources=["CFO", "CTO"],
        ...     evidence=[evidence_ref1, evidence_ref2]
        ... )
    """

    title: str = Field(..., min_length=5, max_length=100, description="Gap title")
    severity: Literal["High", "Medium", "Low"] = Field(..., description="Gap severity")
    description: str = Field(..., min_length=20, max_length=500, description="Detailed description")
    sources: List[str] = Field(..., min_length=1, description="Which roles raised this")
    evidence: List[EvidenceReference] = Field(..., min_length=1, description="Supporting evidence")


class Recommendation(BaseModel):
    """An actionable recommendation with problem→action→metric structure.

    Complies with FR-014: Recommendations must follow "Problem → Action → Metric" format.

    Attributes:
        priority: Priority level (High/Medium/Low)
        problem: Problem statement (10-300 characters)
        action: Action to take (10-300 characters)
        metric: Success metric, must be measurable (10-200 characters)
        source_evidence: Source in debate with complete evidence reference

    Example:
        >>> recommendation = Recommendation(
        ...     priority="High",
        ...     problem="PRD lacks risk assessment section",
        ...     action="Add comprehensive 'Risks & Mitigations' section to PRD",
        ...     metric="PRD includes 5+ identified risks with mitigation strategies",
        ...     source_evidence=evidence_ref
        ... )
    """

    priority: Literal["High", "Medium", "Low"] = Field(..., description="Priority level")
    problem: str = Field(..., min_length=10, max_length=300, description="Problem statement")
    action: str = Field(..., min_length=10, max_length=300, description="Action to take")
    metric: str = Field(..., min_length=10, max_length=200, description="Success metric")
    source_evidence: EvidenceReference = Field(..., description="Source in debate")


# ============================================================================
# Final Output: Enhanced Conclusion
# ============================================================================


class EnhancedConclusion(BaseModel):
    """Complete enhanced conclusion report.

    This is the final output of the enhanced conclusion pipeline,
    containing verdict, role analyses, critical gaps, and recommendations.

    Enforces FR-030 length limits:
    - Maximum 5 critical gaps (all severities)
    - Maximum 5 high-priority recommendations

    Attributes:
        verdict: Verdict with confidence level
        role_analyses: Per-role analyses
        critical_gaps: Identified gaps (max 5)
        recommendations: Actionable recommendations

    Example:
        >>> conclusion = EnhancedConclusion(
        ...     verdict=verdict,
        ...     role_analyses=role_analyses,
        ...     critical_gaps=gaps,
        ...     recommendations=recommendations
        ... )
    """

    verdict: Verdict = Field(..., description="Verdict with confidence")
    role_analyses: List[RoleAnalysis] = Field(..., description="Per-role analyses")
    critical_gaps: List[CriticalGap] = Field(..., description="Identified gaps (max 5)")
    recommendations: List[Recommendation] = Field(..., description="Actionable recommendations")

    @field_validator('critical_gaps')
    @classmethod
    def validate_gap_limit(cls, v: list) -> list:
        """Enforce max 5 gaps per FR-030."""
        if len(v) > 5:
            raise ValueError(f"Maximum 5 gaps allowed, got {len(v)}")
        return v

    @field_validator('recommendations')
    @classmethod
    def validate_high_priority_limit(cls, v: list) -> list:
        """Enforce max 5 high-priority recommendations per FR-030."""
        high_priority_count = sum(1 for r in v if r.priority == "High")
        if high_priority_count > 5:
            raise ValueError(
                f"Maximum 5 high-priority recommendations allowed, got {high_priority_count}"
            )
        return v
