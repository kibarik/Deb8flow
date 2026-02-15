"""
Type definitions for the debate conclusion report feature.

This module provides TypedDict definitions and enums for structured conclusion
reports generated after debates complete. The types support both committee debates
(which parse final_report.md) and standard/document debates (which extract from
debate state).

Example:
    >>> from src.types.conclusion_types import ConclusionData
    >>> conclusion: ConclusionData = {
    ...     "debate_question": "Should we adopt AI?",
    ...     "verdict": {...},
    ...     "qa_summary": [...],
    ...     "tpm_analysis": {...},
    ...     "recommendations": [...],
    ...     "metadata": {...}
    ... }
"""

from typing import TypedDict, List, Optional
from enum import Enum


__all__ = [
    # TypedDict definitions
    "ConclusionData",
    "VerdictSummary",
    "QAPair",
    "TPMAnalysis",
    "TPMWeakness",
    "Recommendation",
    "ConclusionMetadata",
    # Enums
    "DebateType",
    "WeaknessCategory",
    "SeverityLevel",
    "PriorityLevel",
    # Validation functions
    "validate_qa_summary_count",
    "validate_winner_role",
    "validate_severity",
]


# ============================================================================
# Enums
# ============================================================================


class DebateType(str, Enum):
    """Type of debate that generated the conclusion report."""

    STANDARD = "standard"
    DOCUMENT = "document"
    COMMITTEE = "committee"


class WeaknessCategory(str, Enum):
    """Categories of weaknesses that can be identified in a position."""

    UNJUSTIFIED_ASSUMPTION = "unjustified_assumption"
    UNCOVERED_RISK = "uncovered_risk"
    WEAK_METRICS = "weak_metrics"
    MISSING_EVIDENCE = "missing_evidence"
    LOGICAL_FALLACY = "logical_fallacy"
    UNCLEAR_VALUE_PROP = "unclear_value_prop"
    INFEASIBLE_TIMELINE = "infeasible_timeline"
    SELF_IDENTIFIED = "self_identified"


class SeverityLevel(str, Enum):
    """Severity levels for weaknesses and recommendations."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PriorityLevel(str, Enum):
    """Priority levels for recommendations."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================================
# TypedDict Definitions
# ============================================================================


class VerdictSummary(TypedDict):
    """The debate verdict including winner and justification.

    Attributes:
        winner: Role name (e.g., "TPM", "PRO", "CON") or "No clear winner"
        winner_position: "PRO" or "CON" position
        justification: 1-3 sentence explanation of the verdict
        confidence: Optional confidence score from 0.0 to 1.0

    Example:
        >>> verdict: VerdictSummary = {
        ...     "winner": "TPM",
        ...     "winner_position": "PRO",
        ...     "justification": "TPM demonstrated stronger technical feasibility.",
        ...     "confidence": 0.85
        ... }
    """

    winner: str
    winner_position: str
    justification: str
    confidence: Optional[float]


class QAPair(TypedDict):
    """A question-answer pair extracted from the debate.

    Attributes:
        question: Question or challenge posed during debate
        answer: Response or explanation provided
        stage: Stage where this occurred ("opening", "rebuttal", "counter", "final_argument", "verdict")
        speaker: Who provided the answer (e.g., "PRO", "CON", "TPM", "CPO")
        validated: Whether the answer was fact-checked and validated
        priority: Priority from 1-10 (1 = highest priority)

    Example:
        >>> qa: QAPair = {
        ...     "question": "What is the timeline for implementation?",
        ...     "answer": "The implementation can be completed in 6 months.",
        ...     "stage": "opening",
        ...     "speaker": "TPM",
        ...     "validated": True,
        ...     "priority": 3
        ... }
    """

    question: str
    answer: str
    stage: str
    speaker: str
    validated: bool
    priority: int


class TPMWeakness(TypedDict):
    """A specific weakness identified in TPM's position.

    Attributes:
        category: Type of weakness (WeaknessCategory enum value)
        description: Description of the weakness
        severity: Severity level (SeverityLevel enum value)
        source: Who identified this weakness (e.g., "CPO", "CFO", "judge")
        context: Optional additional context about the weakness

    Example:
        >>> weakness: TPMWeakness = {
        ...     "category": "unjustified_assumption",
        ...     "description": "Assumes development team can double velocity",
        ...     "severity": "high",
        ...     "source": "CPO",
        ...     "context": "No historical data supports this claim"
        ... }
    """

    category: str
    description: str
    severity: str
    source: str
    context: Optional[str]


class TPMAnalysis(TypedDict):
    """Analysis of TPM's debate position and identified weaknesses.

    Attributes:
        position_summary: Brief summary of TPM's position
        weaknesses: List of identified weaknesses
        recommended_improvements: List of actionable improvements
        victory_assessment: "won", "lost", or "unclear"

    Example:
        >>> analysis: TPMAnalysis = {
        ...     "position_summary": "TPM argues for 6-month timeline with $100K budget.",
        ...     "weaknesses": [...],
        ...     "recommended_improvements": ["Add historical velocity data"],
        ...     "victory_assessment": "unclear"
        ... }
    """

    position_summary: str
    weaknesses: List[TPMWeakness]
    recommended_improvements: List[str]
    victory_assessment: str


class Recommendation(TypedDict):
    """A recommendation from a debate participant.

    Attributes:
        agent_role: Role name of the agent (e.g., "TPM", "BDM", "CPO", "CFO", "CTO")
        text: Recommendation content (supports "От [Role]:" formatting)
        priority: Optional priority level (PriorityLevel enum value)
        category: Optional category for the recommendation
        actionable: Whether the recommendation is actionable

    Example:
        >>> rec: Recommendation = {
        ...     "agent_role": "CPO",
        ...     "text": "От CPO: Validate timeline with engineering team",
        ...     "priority": "high",
        ...     "category": "planning",
        ...     "actionable": True
        ... }
    """

    agent_role: str
    text: str
    priority: Optional[str]
    category: Optional[str]
    actionable: bool


class ConclusionMetadata(TypedDict):
    """Metadata about the conclusion report.

    Attributes:
        debate_type: Type of debate (DebateType enum value)
        run_id: Unique run identifier for the debate
        generated_at: ISO timestamp of report generation (e.g., "2025-02-15T12:34:56Z")
        source_file: Optional path to final_report.md (for committee debates)
        total_recommendations: Total number of recommendations in the report
        tpm_victory: Whether TPM won the debate
        completion_status: "success", "partial", or "error"
        error_message: Optional error message if completion_status is "error"

    Example:
        >>> metadata: ConclusionMetadata = {
        ...     "debate_type": "committee",
        ...     "run_id": "committee-20250215-123456",
        ...     "generated_at": "2025-02-15T12:34:56Z",
        ...     "source_file": "/path/to/final_report.md",
        ...     "total_recommendations": 5,
        ...     "tpm_victory": False,
        ...     "completion_status": "success",
        ...     "error_message": None
        ... }
    """

    debate_type: str
    run_id: str
    generated_at: str
    source_file: Optional[str]
    total_recommendations: int
    tpm_victory: bool
    completion_status: str
    error_message: Optional[str]


class ConclusionData(TypedDict):
    """Complete conclusion report data extracted from debate results.

    This is the top-level data structure that contains all information
    for a debate conclusion report.

    Attributes:
        debate_question: The debate topic/question
        verdict: Winner and explanation (VerdictSummary)
        qa_summary: Key question-answer pairs (3-10 QAPair objects)
        tpm_analysis: TPM position analysis (TPMAnalysis)
        recommendations: Agent recommendations (0+ Recommendation objects)
        metadata: Report metadata (ConclusionMetadata)

    Example:
        >>> conclusion: ConclusionData = {
        ...     "debate_question": "Should we invest in AI infrastructure?",
        ...     "verdict": {...},
        ...     "qa_summary": [...],
        ...     "tpm_analysis": {...},
        ...     "recommendations": [...],
        ...     "metadata": {...}
        ... }
    """

    debate_question: str
    verdict: VerdictSummary
    qa_summary: List[QAPair]
    tpm_analysis: TPMAnalysis
    recommendations: List[Recommendation]
    metadata: ConclusionMetadata


# ============================================================================
# Validation Functions
# ============================================================================


def validate_qa_summary_count(qa_count: int) -> bool:
    """Validate that QA summary count is within acceptable range.

    Args:
        qa_count: Number of question-answer pairs in the summary

    Returns:
        True if 3 <= qa_count <= 10, False otherwise

    Note:
        Conclusion reports must have between 3 and 10 question-answer pairs
        to ensure comprehensive coverage while maintaining focus.
    """
    return 3 <= qa_count <= 10


def validate_winner_role(winner: str) -> bool:
    """Validate that winner is a valid role name.

    Args:
        winner: The declared winner role name

    Returns:
        True if winner is a valid role, False otherwise

    Valid values:
        - "TPM", "PRO", "CON", "CPO", "CFO", "CTO", "BDM"
        - "No clear winner"
    """
    valid_roles = {
        "TPM",
        "PRO",
        "CON",
        "CPO",
        "CFO",
        "CTO",
        "BDM",
        "No clear winner",
    }
    return winner in valid_roles


def validate_severity(severity: str) -> bool:
    """Validate that severity is a valid severity level.

    Args:
        severity: The severity level to validate

    Returns:
        True if severity is valid, False otherwise

    Valid values:
        - "high", "medium", "low"
    """
    return severity in {"high", "medium", "low"}
