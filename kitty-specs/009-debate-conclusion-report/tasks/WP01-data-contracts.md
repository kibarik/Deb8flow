---
work_package_id: WP01
title: Data Contracts and Types
lane: "for_review"
dependencies: []
base_branch: main
base_commit: c323e8f79c819d9565364f17be33ee0498e47486
created_at: '2026-02-15T09:54:41.393265+00:00'
subtasks:
- T001
- T002
- T003
- T004
- T005
- T006
- T007
phase: Phase 1 - Foundation
assignee: ''
agent: "claude"
shell_pid: "92104"
review_status: ''
reviewed_by: ''
history:
- timestamp: '2026-02-15T09:39:49Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt generated via /spec-kitty.tasks
---

# Work Package Prompt: WP01 – Data Contracts and Types

## Objectives & Success Criteria

Establish type definitions and data contracts for the debate conclusion report feature.

**Success Criteria**:
- All type definitions are importable and pass mypy validation
- Contracts can be instantiated with test data
- Validation functions correctly enforce type constraints
- Unit tests pass for all validation logic

## Context & Constraints

**Prerequisites**: None (foundation package)

**Supporting Documents**:
- `kitty-specs/009-debate-conclusion-report/data-model.md` - Complete entity definitions
- `kitty-specs/009-debate-conclusion-report/research.md` - Research findings
- `src/debate_state.py` - Reference for existing type patterns

**Key Constraints**:
- Must follow existing TypedDict patterns from `src/debate_state.py`
- Use Python 3.12+ typing features
- Support both committee and standard/document debates

## Subtasks & Detailed Guidance

### Subtask T001 – Create conclusion_types.py module

**Purpose**: Establish the module structure for all conclusion-related type definitions.

**Steps**:
1. Create `src/types/conclusion_types.py` (new file)
2. Add module docstring explaining the purpose of the types
3. Import required typing modules: `typing.TypedDict`, `typing.List`, `typing.Optional`, `typing.Enum`
4. Add `__all__` export list for all public types

**Files**:
- `src/types/conclusion_types.py` (new file, ~20 lines initially)

**Validation**:
- [ ] File exists at correct path
- [ ] Module can be imported: `from src.types.conclusion_types import *`

### Subtask T002 – Create core TypedDict definitions

**Purpose**: Define the primary data structures for conclusion reports.

**Steps**:
1. Create `ConclusionData` TypedDict with fields:
   - `debate_question: str`
   - `verdict: VerdictSummary`
   - `qa_summary: List[QAPair]`
   - `tpm_analysis: TPMAnalysis`
   - `recommendations: List[Recommendation]`
   - `metadata: ConclusionMetadata`

2. Create `VerdictSummary` TypedDict with fields:
   - `winner: str` (role name or "No clear winner")
   - `winner_position: str` ("PRO" or "CON")
   - `justification: str` (1-3 sentences)
   - `confidence: Optional[float]` (0.0 to 1.0)

3. Create `QAPair` TypedDict with fields:
   - `question: str`
   - `answer: str`
   - `stage: str` ("opening", "rebuttal", "counter", "final_argument", "verdict")
   - `speaker: str`
   - `validated: bool`
   - `priority: int` (1-10, 1=highest)

**Files**:
- `src/types/conclusion_types.py` (add ~40 lines)

**Validation**:
- [ ] All TypedDict definitions compile without errors
- [ ] Fields match data-model.md specification exactly

### Subtask T003 – Create analysis and weakness TypedDicts

**Purpose**: Define structures for TPM analysis and weakness identification.

**Steps**:
1. Create `TPMAnalysis` TypedDict with fields:
   - `position_summary: str`
   - `weaknesses: List[TPMWeakness]`
   - `recommended_improvements: List[str]`
   - `victory_assessment: str` ("won", "lost", "unclear")

2. Create `TPMWeakness` TypedDict with fields:
   - `category: str` (WeaknessCategory enum value)
   - `description: str`
   - `severity: str` (SeverityLevel enum value)
   - `source: str` (who identified this weakness)
   - `context: Optional[str]`

3. Create `Recommendation` TypedDict with fields:
   - `agent_role: str` ("TPM", "BDM", "CPO", etc.)
   - `text: str`
   - `priority: Optional[str]` (PriorityLevel enum value)
   - `category: Optional[str]`
   - `actionable: bool`

**Files**:
- `src/types/conclusion_types.py` (add ~30 lines)

**Validation**:
- [ ] Weakness categories match research.md findings
- [ ] Recommendation structure supports "От [Role]:" formatting

### Subtask T004 – Create metadata TypedDict

**Purpose**: Define metadata structure for conclusion reports.

**Steps**:
1. Create `ConclusionMetadata` TypedDict with fields:
   - `debate_type: str` (DebateType enum value)
   - `run_id: str`
   - `generated_at: str` (ISO timestamp)
   - `source_file: Optional[str]` (path to final_report.md if applicable)
   - `total_recommendations: int`
   - `tpm_victory: bool`
   - `completion_status: str` ("success", "partial", "error")
   - `error_message: Optional[str]`

2. Add inline examples in docstrings showing expected values

**Files**:
- `src/types/conclusion_types.py` (add ~25 lines)

**Validation**:
- [ ] Metadata supports both committee and standard debates
- [ ] ISO timestamp format is documented

### Subtask T005 – Create enums

**Purpose**: Define enumerated types for categorization.

**Steps**:
1. Create `DebateType` enum with values:
   - `STANDARD = "standard"`
   - `DOCUMENT = "document"`
   - `COMMITTEE = "committee"`

2. Create `WeaknessCategory` enum with values:
   - `UNJUSTIFIED_ASSUMPTION = "unjustified_assumption"`
   - `UNCOVERED_RISK = "uncovered_risk"`
   - `WEAK_METRICS = "weak_metrics"`
   - `MISSING_EVIDENCE = "missing_evidence"`
   - `LOGICAL_FALLACY = "logical_fallacy"`
   - `UNCLEAR_VALUE_PROP = "unclear_value_prop"`
   - `INFEASIBLE_TIMELINE = "infeasible_timeline"`
   - `SELF_IDENTIFIED = "self_identified"`

3. Create `SeverityLevel` enum: `HIGH`, `MEDIUM`, `LOW`
4. Create `PriorityLevel` enum: `HIGH`, `MEDIUM`, `LOW`

**Files**:
- `src/types/conclusion_types.py` (add ~30 lines)

**Validation**:
- [ ] All enum values match data-model.md specification
- [ ] Enums are properly typed as `str` subclasses

### Subtask T006 – Add validation functions

**Purpose**: Provide helper functions to validate type constraints.

**Steps**:
1. Create `validate_qa_summary_count(qa_count: int) -> bool` function:
   - Returns True if 3 <= qa_count <= 10
   - Returns False otherwise
   - Add docstring explaining the constraint

2. Create `validate_winner_role(winner: str) -> bool` function:
   - Accepts: "TPM", "PRO", "CON", "CPO", "CFO", "CTO", "BDM", "No clear winner"
   - Returns True if valid, False otherwise

3. Create `validate_severity(severity: str) -> bool` function:
   - Accepts: "high", "medium", "low"
   - Returns True if valid, False otherwise

**Files**:
- `src/types/conclusion_types.py` (add ~40 lines)

**Validation**:
- [ ] All validation functions have unit tests
- [ ] Functions return correct boolean values

### Subtask T007 – Write unit tests

**Purpose**: Ensure type definitions work correctly and validation functions are tested.

**Steps**:
1. Create `tests/types/test_conclusion_types.py` (new file)
2. Test that all TypedDict can be instantiated with valid data
3. Test that validation functions correctly accept/reject values
4. Test edge cases: empty lists, missing optional fields, boundary values
5. Use pytest fixtures for sample ConclusionData

**Files**:
- `tests/types/test_conclusion_types.py` (new file, ~120 lines)

**Validation**:
- [ ] All tests pass: `pytest tests/types/test_conclusion_types.py`
- [ ] Coverage >90% for type definitions

## Test Strategy

**Unit Tests Required**: Yes (T007)

**Test File**: `tests/types/test_conclusion_types.py`

**Commands**:
```bash
# Run tests
pytest tests/types/test_conclusion_types.py -v

# Run with coverage
pytest tests/types/test_conclusion_types.py --cov=src.types.conclusion_types
```

**Fixtures**: Sample ConclusionData instance for testing

## Risks & Mitigations

**Risk**: Type definitions may evolve during implementation
- **Mitigation**: Keep types flexible with Optional fields

**Risk**: Validation logic may be too strict
- **Mitigation**: Document acceptable values clearly; add examples

## Review Guidance

**Key Acceptance Checkpoints**:
- [ ] All TypedDict match data-model.md specification exactly
- [ ] Enums are properly typed as str subclasses
- [ ] Validation functions are tested
- [ ] Code follows existing patterns from `src/debate_state.py`

**Reviewer Notes**:
- Verify field names and types match data-model.md
- Check that Optional fields are used appropriately
- Validate that enums include all values from research.md

## Activity Log

- 2026-02-15T09:39:49Z – system – lane=planned – Prompt created.

### Valid lanes
`planned`, `doing`, `for_review`, `done`
- 2026-02-15T09:54:41Z – claude – shell_pid=92104 – lane=doing – Assigned agent via workflow command
- 2026-02-15T09:56:52Z – claude – shell_pid=92104 – lane=for_review – Ready for review: Implemented all TypedDict definitions, enums, and validation functions with 30 passing unit tests
