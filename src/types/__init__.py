"""Type definitions for debate conclusion reports."""

from .conclusion_types import (
    ConclusionData,
    VerdictSummary,
    QAPair,
    TPMAnalysis,
    TPMWeakness,
    Recommendation,
    ConclusionMetadata,
    DebateType,
    WeaknessCategory,
    SeverityLevel,
    PriorityLevel,
    validate_qa_summary_count,
    validate_winner_role,
    validate_severity,
)

__all__ = [
    "ConclusionData",
    "VerdictSummary",
    "QAPair",
    "TPMAnalysis",
    "TPMWeakness",
    "Recommendation",
    "ConclusionMetadata",
    "DebateType",
    "WeaknessCategory",
    "SeverityLevel",
    "PriorityLevel",
    "validate_qa_summary_count",
    "validate_winner_role",
    "validate_severity",
]
