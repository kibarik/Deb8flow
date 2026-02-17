# Data Model: Enhanced Committee Debate Conclusion Report

**Feature**: 011-enhanced-committee-debate-conclusion
**Date**: 2025-02-16
**Purpose**: Define Pydantic models for hybrid multi-step LLM pipeline

---

## Overview

The enhanced conclusion pipeline uses a two-stage architecture:
1. **Stage 1 (Extraction)**: Extracts verdict and role analyses into structured intermediate schema
2. **Stage 2 (Synthesis)**: Processes intermediate schema to generate gaps and recommendations

All models use Pydantic for validation and type safety.

---

## Core Models

### EvidenceReference

**Purpose**: Traceable reference to specific debate content (FR-031)

```python
from pydantic import BaseModel, Field, field_validator

class EvidenceReference(BaseModel):
    """Traceable reference to debate content with quote."""

    room_id: str = Field(..., description="Room identifier (e.g., 'TPM_vs_CPO')")
    speaker_role: str = Field(..., description="Speaker who made the statement")
    turn_index: int = Field(..., ge=0, description="Turn number in the debate")
    quote: str = Field(..., max_length=200, description="Supporting quote (max 200 chars)")

    @field_validator('quote')
    @classmethod
    def truncate_quote(cls, v: str) -> str:
        """Truncate quote to max 200 characters."""
        return v[:200] if len(v) > 200 else v
```

**Validation Rules**:
- `room_id`: Must match existing room format (e.g., "TPM_vs_CPO")
- `speaker_role`: Must be valid role (TPM, CPO, CFO, CTO, BDM, PRO, CON, Judge)
- `turn_index`: Non-negative integer
- `quote`: Max 200 characters, auto-truncated

---

### Strength

**Purpose**: Represents a strong argument from a role's perspective

```python
class Strength(BaseModel):
    """A strong argument or point made by a role."""

    description: str = Field(..., min_length=10, max_length=500, description="What was strong")
    evidence: EvidenceReference = Field(..., description="Source of this strength")
```

**Validation Rules**:
- `description`: 10-500 characters, clearly articulated point
- `evidence`: Required traceable reference

---

### Weakness

**Purpose**: Represents a weakness or criticism from a role's perspective

```python
class Weakness(BaseModel):
    """A weakness or criticism identified by a role."""

    description: str = Field(..., min_length=10, max_length=500, description="What was weak")
    evidence: EvidenceReference = Field(..., description="Source of this weakness")
```

**Validation Rules**:
- `description`: 10-500 characters, clearly articulated criticism
- `evidence`: Required traceable reference

---

### RoleAnalysis

**Purpose**: Complete analysis of a single role's perspective

```python
from typing import List
from pydantic import field_validator

class RoleAnalysis(BaseModel):
    """Complete analysis of a role's strengths and weaknesses."""

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
```

**Validation Rules**:
- `role_name`: Must match known role or custom role (FR-025)
- `strengths`: 0-5 items (empty list allowed if no strengths)
- `weaknesses`: 0-5 items (empty list allowed if no weaknesses)

**FR-030 Compliance**: Enforces maximum 5 bullets each for strengths/weaknesses

---

### Verdict

**Purpose**: Clear answer to user's question with confidence level

```python
from typing import Literal

class Verdict(BaseModel):
    """Clear verdict answering the user's question."""

    answer: str = Field(..., min_length=20, max_length=1000, description="Direct answer")
    confidence: Literal["High", "Medium", "Low"] = Field(..., description="Confidence level per FR-029")
    rationale: str = Field(..., min_length=50, max_length=500, description="2-3 sentence explanation")
    room_outcomes: str = Field(..., description="Summary of outcomes across rooms")

    @field_validator('answer')
    @classmethod
    def validate_word_count(cls, v: str) -> str:
        """Enforce 120-150 word limit per FR-030."""
        word_count = len(v.split())
        if word_count < 120 or word_count > 150:
            raise ValueError(f"Answer must be 120-150 words, got {word_count}")
        return v
```

**Validation Rules**:
- `answer`: 120-150 words (enforced per FR-030)
- `confidence`: Must be one of "High", "Medium", "Low"
- `rationale`: 50-500 characters (2-3 sentences)
- `room_outcomes`: Free text describing room outcomes

**FR-029 Compliance**: Confidence calculated separately before model instantiation

---

### IntermediateConclusionSchema

**Purpose**: Complete output from Stage 1 (extraction phase)

```python
class IntermediateConclusionSchema(BaseModel):
    """Structured schema after Stage 1 extraction."""

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
```

**Validation Rules**:
- `verdict`: Required
- `role_analyses`: At least 1 role, no duplicates

**Stage 1 Output**: This is the input to Stage 2 synthesis

---

## Stage 2 Output Models

### CriticalGap

**Purpose**: A significant weakness or risk identified across multiple roles

```python
class CriticalGap(BaseModel):
    """A critical gap identified across debate participants."""

    title: str = Field(..., min_length=5, max_length=100, description="Gap title")
    severity: Literal["High", "Medium", "Low"] = Field(..., description="Gap severity")
    description: str = Field(..., min_length=20, max_length=500, description="Detailed description")
    sources: List[str] = Field(..., min_length=1, description="Which roles raised this")
    evidence: List[EvidenceReference] = Field(..., min_length=1, description="Supporting evidence")
```

**Validation Rules**:
- `title`: 5-100 characters
- `severity`: Must be one of "High", "Medium", "Low"
- `description`: 20-500 characters
- `sources`: At least 1 role name
- `evidence`: At least 1 evidence reference

**FR-011 Compliance**: Severity ranked by number of sources, argument strength, judge emphasis

---

### Recommendation

**Purpose**: Actionable improvement with problem→action→metric structure

```python
class Recommendation(BaseModel):
    """An actionable recommendation with metric."""

    priority: Literal["High", "Medium", "Low"] = Field(..., description="Priority level")
    problem: str = Field(..., min_length=10, max_length=300, description="Problem statement")
    action: str = Field(..., min_length=10, max_length=300, description="Action to take")
    metric: str = Field(..., min_length=10, max_length=200, description="Success metric")
    source_evidence: EvidenceReference = Field(..., description="Source in debate")
```

**Validation Rules**:
- `priority`: Must be one of "High", "Medium", "Low"
- `problem`: 10-300 characters
- `action`: 10-300 characters
- `metric`: 10-200 characters, must be measurable
- `source_evidence`: Required traceable reference

**FR-014 Compliance**: "Problem → Action → Metric" format enforced

---

### EnhancedConclusion

**Purpose**: Complete output from Stage 2 (final enhanced conclusion)

```python
class EnhancedConclusion(BaseModel):
    """Complete enhanced conclusion report."""

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
            raise ValueError(f"Maximum 5 high-priority recommendations allowed, got {high_priority_count}")
        return v
```

**Validation Rules**:
- `verdict`: Required
- `role_analyses`: Required (from Stage 1)
- `critical_gaps`: Max 5 items (FR-030)
- `recommendations`: Max 5 high-priority items (FR-030)

---

## Confidence Calculation (FR-029)

**Formula** (implemented outside Pydantic, set on Verdict model):

```python
def calculate_confidence(room_outcomes: dict, judge_rationales: list[str]) -> str:
    """
    Calculate confidence level per FR-029.

    Args:
        room_outcomes: Dict mapping room_id to winner (e.g., {"TPM_vs_CPO": "CON"})
        judge_rationales: List of judge rationale texts

    Returns:
        "High", "Medium", or "Low"
    """
    # Count wins/losses
    tpm_wins = sum(1 for winner in room_outcomes.values() if winner == "PRO")
    total_rooms = len(room_outcomes)

    # Check for strong contradictions in rationales
    has_contradictions = _detect_strong_contradictions(judge_rationales)

    # Base confidence from vote distribution
    if total_rooms == 0:
        base_confidence = "Low"
    elif tpm_wins == total_rooms or tpm_wins == 0:
        base_confidence = "High"  # Unanimous (4-0 or 0-4)
    elif abs(tpm_wins - total_rooms / 2) <= 0.5:
        base_confidence = "Low"   # Tie (2-2)
    else:
        base_confidence = "Medium"  # Split (3-1 or 1-3)

    # Reduce by one level if strong contradictions detected
    if has_contradictions and base_confidence == "High":
        return "Medium"
    elif has_contradictions and base_confidence == "Medium":
        return "Low"

    return base_confidence

def _detect_strong_contradictions(rationales: list[str]) -> bool:
    """Detect if judge rationales contain strong contradictions."""
    # Implementation: Look for opposing keywords, conflicting assessments
    contradiction_keywords = ["however", "contradicts", "inconsistent", "conflicting"]
    combined = " ".join(rationales).lower()
    return sum(1 for kw in contradiction_keywords if kw in combined) >= 2
```

---

## Model Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                  Enhanced Conclusion                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────┐                                              │
│  │  Verdict   │                                              │
│  │  - answer  │                                              │
│  │  - confidence│                                           │
│  │  - rationale│                                           │
│  └────────────┘                                              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            RoleAnalysis[]                             │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  ┌─────────────┐  ┌────────────────────────────────┐ │   │
│  │  │ Strengths[] │  │ Weaknesses[]                    │ │   │
│  │  │ - description│  │ - description                   │ │   │
│  │  │ - evidence   │  │ - evidence                      │ │   │
│  │  │   ┌─────┐   │  │   ┌─────┐                       │ │   │
│  │  │   │Ref  │   │  │   │Ref  │                       │ │   │
│  │  │   └─────┘   │  │   └─────┘                       │ │   │
│  │  └─────────────┘  └────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            CriticalGap[] (max 5)                      │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  - title                                               │   │
│  │  - severity                                            │   │
│  │  - description                                         │   │
│  │  - sources[] (role names)                              │   │
│  │  - evidence[] (EvidenceReference[])                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Recommendation[]                           │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  - priority (High/Medium/Low)                         │   │
│  │  - problem                                            │   │
│  │  - action                                             │   │
│  │  - metric                                             │   │
│  │  - source_evidence (EvidenceReference)                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┐
│    EvidenceReference             │
├──────────────────────────────────┤
│  - room_id                       │
│  - speaker_role                  │
│  - turn_index                    │
│  - quote (max 200 chars)         │
└──────────────────────────────────┘
```

---

## Type Export

All models will be exported from `src/types/conclusion_types.py`:

```python
# src/types/conclusion_types.py

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

# Model implementations above...
```

---

## Validation Summary

| Model | Key Validations | FR Compliance |
|-------|-----------------|---------------|
| EvidenceReference | quote max 200 chars | FR-031 |
| RoleAnalysis | strengths/weaknesses max 5 | FR-030 |
| Verdict | answer 120-150 words | FR-030, FR-029 |
| IntermediateConclusionSchema | unique roles, min 1 role | - |
| CriticalGap | min 1 source, min 1 evidence | FR-011 |
| Recommendation | measurable metric required | FR-014, FR-016 |
| EnhancedConclusion | max 5 gaps, max 5 high-priority | FR-030 |

---

*Data Model: 2025-02-16*
