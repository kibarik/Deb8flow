# Data Model: Debate Conclusion Report Feature

**Feature**: 009-debate-conclusion-report
**Date**: 2025-02-15
**Mission**: software-dev

## Overview

This document defines the data structures and entities for the debate conclusion report feature. The model supports both committee debates (which parse `final_report.md`) and standard/document debates (which extract from debate state).

---

## Core Entities

### 1. ConclusionData

**Purpose**: Complete conclusion report data structure

**Attributes**:
```python
class ConclusionData(TypedDict):
    """Complete conclusion report data extracted from debate results"""
    debate_question: str              # The debate topic/question
    verdict: VerdictSummary           # Winner and explanation
    qa_summary: List[QAPair]          # Key question-answer pairs (3-10)
    tpm_analysis: TPMAnalysis         # TPM position analysis
    recommendations: List[Recommendation]  # Agent recommendations
    metadata: ConclusionMetadata      # Report metadata
```

**Relationships**:
- Contains 1 VerdictSummary
- Contains 3-10 QAPair objects
- Contains 1 TPMAnalysis
- Contains 0+ Recommendation objects
- Contains 1 ConclusionMetadata

**Lifecycle**: Created at debate completion, immutable

---

### 2. VerdictSummary

**Purpose**: Debate winner and justification

**Attributes**:
```python
class VerdictSummary(TypedDict):
    """The debate verdict"""
    winner: str                       # Role name or "No clear winner"
    winner_position: str              # "PRO" or "CON"
    justification: str                # 1-3 sentence explanation
    confidence: Optional[float]       # Optional confidence score (0-1)
```

**Valid Values**:
- `winner`: "TPM", "PRO", "CON", "CPO", "CFO", "CTO", "BDM", "No clear winner"
- `winner_position`: "PRO" or "CON"
- `confidence`: 0.0 to 1.0 (optional)

---

### 3. QAPair

**Purpose**: A question-answer pair from the debate

**Attributes**:
```python
class QAPair(TypedDict):
    """A question-answer pair extracted from debate"""
    question: str                     # Question or challenge
    answer: str                       # Response or explanation
    stage: DebateStage                # Stage where this occurred
    speaker: str                      # Who provided the answer
    validated: bool                   # Whether the answer was fact-checked
    priority: int                     # 1-10 (1 = highest priority)
```

**Valid Values**:
- `stage`: "opening", "rebuttal", "counter", "final_argument", "verdict"
- `speaker`: "PRO", "CON", "judge", or role names (TPM, CPO, etc.)
- `priority`: 1-10

---

### 4. TPMAnalysis

**Purpose**: Analysis of TPM's position and weaknesses

**Attributes**:
```python
class TPMAnalysis(TypedDict):
    """Analysis of TPM's debate position"""
    position_summary: str             # Brief summary of TPM's position
    weaknesses: List[TPMWeakness]     # Identified weaknesses
    recommended_improvements: List[str]  # Actionable improvements
    victory_assessment: str           # "won", "lost", or "unclear"
```

**Valid Values**:
- `victory_assessment`: "won", "lost", "unclear"

---

### 5. TPMWeakness

**Purpose**: A specific weakness in TPM's position

**Attributes**:
```python
class TPMWeakness(TypedDict):
    """A weakness identified in TPM's position"""
    category: WeaknessCategory        # Type of weakness
    description: str                  # Description of the weakness
    severity: SeverityLevel           # Severity level
    source: str                       # Who identified this weakness
    context: Optional[str]            # Additional context
```

**Valid Values**:
- `category`: "unjustified_assumption", "uncovered_risk", "weak_metrics", "missing_evidence", "logical_fallacy", "unclear_value_prop", "infeasible_timeline", "self_identified"
- `severity`: "high", "medium", "low"
- `source`: "judge", "CPO", "CFO", "CTO", "BDM", "TPM", "PRO", "CON"

---

### 6. Recommendation

**Purpose**: A recommendation from a debate participant

**Attributes**:
```python
class Recommendation(TypedDict):
    """A recommendation from a debate participant"""
    agent_role: str                   # Role name of the agent
    text: str                         # Recommendation content
    priority: Optional[PriorityLevel] # Optional priority level
    category: Optional[str]           # Optional category
    actionable: bool                  # Whether the recommendation is actionable
```

**Valid Values**:
- `agent_role`: "TPM", "BDM", "CPO", "CFO", "CTO", "PRO", "CON", "judge"
- `priority`: "high", "medium", "low"
- `actionable`: true/false

---

### 7. ConclusionMetadata

**Purpose**: Metadata about the conclusion report

**Attributes**:
```python
class ConclusionMetadata(TypedDict):
    """Metadata about the conclusion report"""
    debate_type: DebateType           # Type of debate
    run_id: str                       # Unique run identifier
    generated_at: str                 # ISO timestamp
    source_file: Optional[str]        # final_report.md path (if applicable)
    total_recommendations: int        # Total number of recommendations
    tpm_victory: bool                 # Whether TPM won
    completion_status: str            # "success" or "error"
    error_message: Optional[str]      # Error message if failed
```

**Valid Values**:
- `debate_type`: "standard", "document", "committee"
- `completion_status`: "success", "partial", "error"

---

## Relationships

### Entity Relationship Diagram

```
ConclusionData
├── VerdictSummary (1)
├── List[QAPair] (3-10)
├── TPMAnalysis (1)
│   └── List[TPMWeakness] (0+)
├── List[Recommendation] (0+)
└── ConclusionMetadata (1)
```

---

## Validation Rules

### ConclusionData Validation

| Rule | Description |
|------|-------------|
| CD-001 | `debate_question` must be non-empty |
| CD-002 | `qa_summary` must contain 3-10 pairs |
| CD-003 | `verdict.winner` must be valid role or "No clear winner" |
| CD-004 | `recommendations` must have unique agent_role + text combinations |
| CD-005 | `metadata.generated_at` must be valid ISO timestamp |

---

## Storage & Persistence

### File Format

**Conclusion.md**: Markdown format with structured sections (see spec.md for full structure)

### Storage Location

**Committee Debates**: `committee_output/{run_id}/Conclusion.md`
**Standard/Document Debates**: `debates_output/{run_id}/Conclusion.md`

---

## Complete Type Definitions (Python)

```python
from typing import TypedDict, List, Optional
from enum import Enum

class DebateStage(str, Enum):
    OPENING = "opening"
    REBUTTAL = "rebuttal"
    COUNTER = "counter"
    FINAL_ARGUMENT = "final_argument"
    VERDICT = "verdict"

class WeaknessCategory(str, Enum):
    UNJUSTIFIED_ASSUMPTION = "unjustified_assumption"
    UNCOVERED_RISK = "uncovered_risk"
    WEAK_METRICS = "weak_metrics"
    MISSING_EVIDENCE = "missing_evidence"
    LOGICAL_FALLACY = "logical_fallacy"
    UNCLEAR_VALUE_PROP = "unclear_value_prop"
    INFEASIBLE_TIMELINE = "infeasible_timeline"
    SELF_IDENTIFIED = "self_identified"

class SeverityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class PriorityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class DebateType(str, Enum):
    STANDARD = "standard"
    DOCUMENT = "document"
    COMMITTEE = "committee"

class VerdictSummary(TypedDict):
    winner: str
    winner_position: str
    justification: str
    confidence: Optional[float]

class QAPair(TypedDict):
    question: str
    answer: str
    stage: DebateStage
    speaker: str
    validated: bool
    priority: int

class TPMWeakness(TypedDict):
    category: WeaknessCategory
    description: str
    severity: SeverityLevel
    source: str
    context: Optional[str]

class TPMAnalysis(TypedDict):
    position_summary: str
    weaknesses: List[TPMWeakness]
    recommended_improvements: List[str]
    victory_assessment: str

class Recommendation(TypedDict):
    agent_role: str
    text: str
    priority: Optional[PriorityLevel]
    category: Optional[str]
    actionable: bool

class ConclusionMetadata(TypedDict):
    debate_type: DebateType
    run_id: str
    generated_at: str
    source_file: Optional[str]
    total_recommendations: int
    tpm_victory: bool
    completion_status: str
    error_message: Optional[str]

class ConclusionData(TypedDict):
    debate_question: str
    verdict: VerdictSummary
    qa_summary: List[QAPair]
    tpm_analysis: TPMAnalysis
    recommendations: List[Recommendation]
    metadata: ConclusionMetadata
```
