# Data Model: PRD Completeness Validator

**Feature**: 010-prd-completeness-validator
**Date**: 2025-02-15
**Phase**: Phase 1 - Design & Contracts

## Overview

This document defines the data structures used in the PRD Completeness Validator feature. All models use Pydantic for validation and structured output from the LLM.

## Core Models

### PRDValidationResult

The primary output from the validation process.

```python
from typing import List, Optional
from pydantic import BaseModel, Field

class PRDValidationResult(BaseModel):
    """Complete validation result for a PRD document."""

    overall_score: int = Field(
        ...,
        ge=0,
        le=10,
        description="Overall PRD completeness score from 0-10"
    )

    section_analysis: List["SectionAnalysis"] = Field(
        ...,
        description="Analysis of each section in the PRD template"
    )

    recommendations: List[str] = Field(
        ...,
        description="Actionable recommendations for improving the PRD",
        min_length=1,
        max_length=10
    )

    missing_sections: List[str] = Field(
        default_factory=list,
        description="List of required sections not found in the PRD"
    )

    underdeveloped_sections: List[str] = Field(
        default_factory=list,
        description="List of sections present but needing more detail"
    )

    present_sections: List[str] = Field(
        default_factory=list,
        description="List of required sections found in the PRD"
    )

    total_sections: int = Field(
        ...,
        description="Total number of required sections in the template"
    )

    coherence_score: float = Field(
        ...,
        ge=0.0,
        le=2.0,
        description="Coherence score (0-2) measuring logical flow between sections"
    )
```

### SectionAnalysis

Detailed analysis for a single PRD section.

```python
from typing import Literal, Optional

class SectionAnalysis(BaseModel):
    """Analysis of a single PRD section."""

    section_name: str = Field(
        ...,
        description="Name of the section being analyzed"
    )

    status: Literal["present", "missing", "underdeveloped"] = Field(
        ...,
        description="Whether the section is present, missing, or needs more work"
    )

    content_quality: Optional[str] = Field(
        None,
        description="AI assessment of content quality (null if missing)"
    )

    word_count: int = Field(
        ...,
        ge=0,
        description="Number of words in the section content"
    )

    bullet_count: int = Field(
        ...,
        ge=0,
        description="Number of bullet points in the section"
    )

    suggestions: List[str] = Field(
        default_factory=list,
        description="Specific suggestions for improving this section"
    )

    required: bool = Field(
        ...,
        description="Whether this section is required or optional"
    )
```

### PRDTemplate

Definition of the required PRD structure.

```python
from typing import Dict, Any

PRD_TEMPLATE: Dict[str, Dict[str, Any]] = {
    "Executive Summary": {
        "required": True,
        "description": "Problem, Solution, Success Criteria",
        "keywords": ["problem", "solution", "summary"],
        "min_words": 50
    },
    "Background & Context": {
        "required": True,
        "description": "Market situation, User pain points",
        "keywords": ["background", "context", "market"],
        "min_words": 100
    },
    "Goals & Success Metrics": {
        "required": True,
        "description": "SMART objectives, Key metrics",
        "keywords": ["goals", "metrics", "success", "objectives"],
        "min_words": 50
    },
    "User Personas": {
        "required": True,
        "description": "Target users, Use cases",
        "keywords": ["personas", "users", "audience"],
        "min_words": 50
    },
    "Functional Requirements": {
        "required": True,
        "description": "Core features, User stories",
        "keywords": ["requirements", "features", "functionality"],
        "min_words": 100
    },
    "Non-Functional Requirements": {
        "required": True,
        "description": "Performance, Security, Scalability",
        "keywords": ["performance", "security", "scalability", "non-functional"],
        "min_words": 50
    },
    "Technical Constraints": {
        "required": True,
        "description": "Tech stack limitations, Integrations",
        "keywords": ["constraints", "technical", "stack", "integrations"],
        "min_words": 50
    },
    "Risks & Mitigations": {
        "required": True,
        "description": "Known risks, Contingency plans",
        "keywords": ["risks", "mitigations", "contingency"],
        "min_words": 50
    },
    "Timeline & Milestones": {
        "required": True,
        "description": "Phases, Key dates",
        "keywords": ["timeline", "milestones", "schedule", "phases"],
        "min_words": 50
    },
    "Open Questions": {
        "required": True,
        "description": "Unresolved items, Decision points",
        "keywords": ["questions", "unresolved", "decisions"],
        "min_words": 30
    }
}
```

## State Management

### PRDValidatorState

State passed to/from the PRD validator node (if integrated into LangGraph workflow).

```python
from typing import Optional, TypedDict

class PRDValidatorState(TypedDict):
    """State for PRD validation within a LangGraph workflow."""

    prd_file_path: str
    output_format: Literal["console", "file", "both"]
    validation_result: Optional[PRDValidationResult]
    report_file_path: Optional[str]
    error: Optional[str]
    prompt_tokens: int
    completion_tokens: int
```

## Data Flow

```
┌─────────────┐
│  CLI Input  │
│  --check-prd│
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Parse Markdown File │
│ Extract Sections    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Quantitative Score  │
│ (Presence, Depth)   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ LLM Assessment      │
│ (Coherence, Quality)│
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Generate Report     │
│ (Console + File)    │
└─────────────────────┘
```

## Validation Rules

### Scoring Algorithm (from FR-002)

```python
def calculate_overall_score(
    presence_score: float,  # 0-4 (40%)
    depth_score: float,     # 0-4 (40%)
    coherence_score: float  # 0-2 (20%)
) -> int:
    """Calculate overall score from components."""
    raw_score = presence_score + depth_score + coherence_score
    return round(raw_score)

# Score bands
def get_score_band(score: int) -> str:
    """Get descriptive score band."""
    if score >= 9:
        return "Excellent"
    elif score >= 7:
        return "Good"
    elif score >= 5:
        return "Adequate"
    elif score >= 3:
        return "Poor"
    else:
        return "Fail"
```

### Section Status Determination

```python
def determine_section_status(
    section_name: str,
    content: str,
    template_entry: dict
) -> Literal["present", "missing", "underdeveloped"]:
    """Determine the status of a section."""

    if not content or not content.strip():
        return "missing"

    word_count = len(content.split())
    min_words = template_entry.get("min_words", 50)

    if word_count < min_words:
        return "underdeveloped"

    return "present"
```

## Report Generation Models

### ConsoleReportFormat

Structure for console output (not a Pydantic model, but a formatting specification).

```python
CONSOLE_REPORT_FORMAT = """
📋 PRD Validation Report
═══════════════════════════════════════════
File: {prd_path}
Score: {overall_score}/10 ({score_band})

✅ Present Sections ({present_count}/{total_sections}):
  • Executive Summary
  • Background & Context
  ...

❌ Missing Sections ({missing_count}):
  • Risks & Mitigations
  • Open Questions

⚠️  Underdeveloped Sections:
  • User Personas (insufficient detail on use cases)

💡 Top Recommendations:
  1. Add "Risks & Mitigations" section
  2. Expand "User Personas" with specific scenarios
  ...

📄 Detailed report: {report_path}
"""
```

### MarkdownReportFormat

Structure for `prd_review.md` output.

```python
MARKDOWN_REPORT_FORMAT = """
# PRD Validation Report

## Executive Summary

**Overall Score**: {overall_score}/10 ({score_band})

**Assessment**: {one_paragraph_assessment}

## Section-by-Section Analysis

### {section_name}
- **Status**: {status}
- **Word Count**: {word_count}
- **Quality**: {content_quality}
- **Suggestions**:
  - {suggestion_1}
  - {suggestion_2}

...

## Recommendations by Priority

### High Priority
- [ ] {recommendation_1}
- [ ] {recommendation_2}

### Medium Priority
- [ ] {recommendation_3}

...

## Best Practices Reference

*Link to example well-written PRD sections*

## Next Steps

1. Address missing sections
2. Expand underdeveloped sections
3. Re-run validation: `python main.py --check-prd {prd_path}`
"""
```

## Usage Example

```python
from nodes.prd_validator_node import PRDValidatorNode
from configurations.llm_config import OpenAILLMConfig

# Initialize node
config = OpenAILLMConfig(
    model_name="gpt-4",
    openai_api_key="sk-..."
)
validator = PRDValidatorNode(llm_config=config)

# Validate PRD
result = validator.validate_prd(
    prd_path="path/to/prd.md",
    output_format="both"
)

# Access results
print(f"Score: {result['validation_result'].overall_score}/10")
print(f"Report: {result['report_file_path']}")
print(f"Tokens: {result['prompt_tokens']} + {result['completion_tokens']}")
```

## References

1. **Specification**: `kitty-specs/010-prd-completeness-validator/spec.md`
2. **Research**: `kitty-specs/010-prd-completeness-validator/research.md`
3. **Pydantic Documentation**: https://docs.pydantic.dev/
