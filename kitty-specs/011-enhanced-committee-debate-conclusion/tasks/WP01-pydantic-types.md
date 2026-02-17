---
work_package_id: WP01
title: Foundation - Pydantic Types for Enhanced Conclusion
lane: "done"
dependencies: []
base_branch: main
base_commit: 9d5705de96b438c1c93f45e8d9bcaad029b92cfe
created_at: '2026-02-15T22:27:55.727861+00:00'
subtasks:
- T001
- T002
- T003
- T004
- T005
- T006
phase: Phase 1 - Foundation
assignee: ''
agent: "claude"
shell_pid: "84523"
review_status: "approved"
reviewed_by: "ALeks ishmanov"
history:
- timestamp: '2025-02-16T12:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt generated via /spec-kitty.tasks
---

# Work Package Prompt: WP01 – Foundation - Pydantic Types for Enhanced Conclusion

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_status` field above. If it says `has_feedback`, scroll to the **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- **Mark as acknowledged**: When you understand the feedback and begin addressing it, update `review_status: acknowledged` in the frontmatter.
- **Report progress**: As you address each feedback item, update the Activity Log explaining what you changed.

---

## Review Feedback

> **Populated by `/spec-kitty.review`** – Reviewers add detailed feedback here when work needs changes. Implementation must address every item listed below before returning for re-review.

*[This section is empty initially. Reviewers will populate it if the work is returned from review. If you see feedback here, treat each item as a must-do before completion.]*

---

## Markdown Formatting
Wrap HTML/XML tags in backticks: `` `<div>` ``, `` `<script>` ``
Use language identifiers in code blocks: ````python`, ````bash`

---

## Objectives & Success Criteria

**Objectives**:
1. Create Pydantic models for enhanced conclusion pipeline with full type safety
2. Implement validators for FR-030 length limits (60-second readability)
3. Implement validators for FR-031 evidence reference format
4. Support both Russian and English content with UTF-8 encoding

**Success Criteria**:
- All Pydantic models defined with proper field constraints
- EvidenceReference enforces max 200 char quote with auto-truncation
- RoleAnalysis enforces 3-5 bullets max for strengths/weaknesses
- Verdict enforces 120-150 word limit for answer
- EnhancedConclusion enforces max 5 gaps and max 5 high-priority recommendations
- Unit tests verify all validators work correctly

---

## Context & Constraints

**Supporting Documents**:
- Spec: `kitty-specs/011-enhanced-committee-debate-conclusion/spec.md` (FR-026 to FR-031)
- Data Model: `kitty-specs/011-enhanced-committee-debate-conclusion/data-model.md` (complete schema definitions)
- Plan: `kitty-specs/011-enhanced-committee-debate-conclusion/plan.md` (architecture overview)

**Existing Code**:
- Current types in `src/types/conclusion_types.py` (TypedDict based)
- Project uses Pydantic v2 for validation

**Constraints**:
- Must use Pydantic v2 syntax (Field, field_validator, not ConfigDict)
- All models must support UTF-8 encoding for Russian/English content
- Validators must raise clear ValidationError messages
- Models must be serializable to JSON for LLM integration

**Architectural Decisions**:
- Create new file `src/types/enhanced_conclusion_types.py` (separate from existing conclusion_types.py)
- Use Literal types for fixed values (High/Medium/Low, TPM/CPO/etc.)
- Auto-truncate quotes to 200 chars rather than raising error

---

## Subtasks & Detailed Guidance

### Subtask T001 – EvidenceReference Model (FR-031 Compliance)
- **Purpose**: Traceable reference to specific debate content with all required fields
- **Steps**:
  1. Create `src/types/enhanced_conclusion_types.py`
  2. Import from pydantic: BaseModel, Field, field_validator
  3. Import from typing: List, Literal
  4. Define EvidenceReference class:
     ```python
     class EvidenceReference(BaseModel):
         room_id: str = Field(..., description="Room identifier (e.g., 'TPM_vs_CPO')")
         speaker_role: str = Field(..., description="Speaker who made the statement")
         turn_index: int = Field(..., ge=0, description="Turn number in the debate")
         quote: str = Field(..., max_length=200, description="Supporting quote (max 200 chars)")

         @field_validator('quote')
         @classmethod
         def truncate_quote(cls, v: str) -> str:
             return v[:200] if len(v) > 200 else v
     ```
  5. Add docstring explaining FR-031 compliance
  6. Test with quotes > 200 chars to verify truncation

**Files**:
- `src/types/enhanced_conclusion_types.py` (new file, ~50 lines)

**Parallel?**: No (foundational)

**Notes**:
- Auto-truncation is preferred over error for better UX
- room_id format: "TPM_vs_CPO", "TPM_vs_CFO", etc.
- speaker_role values: "TPM", "CPO", "CFO", "CTO", "BDM", "PRO", "CON", "Judge"

---

### Subtask T002 – Strength, Weakness, RoleAnalysis Models (FR-030 Compliance)
- **Purpose**: Role-based analysis with 3-5 bullet limit enforcement
- **Steps**:
  1. Add Strength class:
     ```python
     class Strength(BaseModel):
         description: str = Field(..., min_length=10, max_length=500, description="What was strong")
         evidence: EvidenceReference = Field(..., description="Source of this strength")
     ```
  2. Add Weakness class:
     ```python
     class Weakness(BaseModel):
         description: str = Field(..., min_length=10, max_length=500, description="What was weak")
         evidence: EvidenceReference = Field(..., description="Source of this weakness")
     ```
  3. Add RoleAnalysis class with validator:
     ```python
     class RoleAnalysis(BaseModel):
         role_name: str = Field(..., description="Role name (e.g., 'TPM', 'CPO')")
         strengths: List[Strength] = Field(default_factory=list, description="Strong points (3-5 max)")
         weaknesses: List[Weakness] = Field(default_factory=list, description="Weak points (3-5 max)")

         @field_validator('strengths', 'weaknesses')
         @classmethod
         def validate_length(cls, v: list) -> list:
             if len(v) > 5:
                 raise ValueError(f"Maximum 5 items allowed, got {len(v)}")
             return v
     ```
  4. Add __all__ export for these classes

**Files**:
- `src/types/enhanced_conclusion_types.py` (extend, ~40 lines)

**Parallel?**: No

**Notes**:
- Empty list allowed for strengths/weaknesses (0-5 range)
- Validator checks both strengths and weaknesses
- Error message must be clear about the 5-item limit

---

### Subtask T003 – Verdict and IntermediateConclusionSchema Models
- **Purpose**: Verdict with confidence and word count validation
- **Steps**:
  1. Add Verdict class:
     ```python
     class Verdict(BaseModel):
         answer: str = Field(..., min_length=20, max_length=1000, description="Direct answer")
         confidence: Literal["High", "Medium", "Low"] = Field(..., description="Confidence level per FR-029")
         rationale: str = Field(..., min_length=50, max_length=500, description="2-3 sentence explanation")
         room_outcomes: str = Field(..., description="Summary of outcomes across rooms")

         @field_validator('answer')
         @classmethod
         def validate_word_count(cls, v: str) -> str:
             word_count = len(v.split())
             if word_count < 120 or word_count > 150:
                 raise ValueError(f"Answer must be 120-150 words, got {word_count}")
             return v
     ```
  2. Add IntermediateConclusionSchema class:
     ```python
     class IntermediateConclusionSchema(BaseModel):
         verdict: Verdict = Field(..., description="Verdict with confidence")
         role_analyses: List[RoleAnalysis] = Field(..., min_length=1, description="Per-role analyses")

         @field_validator('role_analyses')
         @classmethod
         def validate_unique_roles(cls, v: list) -> list:
             role_names = [r.role_name for r in v]
             if len(role_names) != len(set(role_names)):
                 raise ValueError("Duplicate role names detected")
             return v
     ```

**Files**:
- `src/types/enhanced_conclusion_types.py` (extend, ~40 lines)

**Parallel?**: No

**Notes**:
- Word count validator splits on whitespace (simple but effective)
- Duplicate role check prevents data quality issues
- confidence uses Literal type for type safety

---

### Subtask T004 – CriticalGap and Recommendation Models
- **Purpose**: Gaps and recommendations with severity/priority enums
- **Steps**:
  1. Add CriticalGap class:
     ```python
     class CriticalGap(BaseModel):
         title: str = Field(..., min_length=5, max_length=100, description="Gap title")
         severity: Literal["High", "Medium", "Low"] = Field(..., description="Gap severity")
         description: str = Field(..., min_length=20, max_length=500, description="Detailed description")
         sources: List[str] = Field(..., min_length=1, description="Which roles raised this")
         evidence: List[EvidenceReference] = Field(..., min_length=1, description="Supporting evidence")
     ```
  2. Add Recommendation class:
     ```python
     class Recommendation(BaseModel):
         priority: Literal["High", "Medium", "Low"] = Field(..., description="Priority level")
         problem: str = Field(..., min_length=10, max_length=300, description="Problem statement")
         action: str = Field(..., min_length=10, max_length=300, description="Action to take")
         metric: str = Field(..., min_length=10, max_length=200, description="Success metric")
         source_evidence: EvidenceReference = Field(..., description="Source in debate")
     ```

**Files**:
- `src/types/enhanced_conclusion_types.py` (extend, ~30 lines)

**Parallel?**: No

**Notes**:
- sources is List[str] of role names
- Each gap must have at least 1 source and 1 evidence
- metric must be measurable (validated in WP10, not here)

---

### Subtask T005 – EnhancedConclusion Aggregate Model
- **Purpose**: Complete output with max limit validators
- **Steps**:
  1. Add EnhancedConclusion class:
     ```python
     class EnhancedConclusion(BaseModel):
         verdict: Verdict = Field(..., description="Verdict with confidence")
         role_analyses: List[RoleAnalysis] = Field(..., description="Per-role analyses")
         critical_gaps: List[CriticalGap] = Field(..., description="Identified gaps (max 5)")
         recommendations: List[Recommendation] = Field(..., description="Actionable recommendations")

         @field_validator('critical_gaps')
         @classmethod
         def validate_gap_limit(cls, v: list) -> list:
             if len(v) > 5:
                 raise ValueError(f"Maximum 5 gaps allowed, got {len(v)}")
             return v

         @field_validator('recommendations')
         @classmethod
         def validate_high_priority_limit(cls, v: list) -> list:
             high_priority_count = sum(1 for r in v if r.priority == "High")
             if high_priority_count > 5:
                 raise ValueError(f"Maximum 5 high-priority recommendations allowed, got {high_priority_count}")
             return v
     ```
  2. Update __all__ to export all classes

**Files**:
- `src/types/enhanced_conclusion_types.py` (extend, ~30 lines)

**Parallel?**: No

**Notes**:
- Only high-priority recommendations are limited to 5
- Medium/Low recommendations have no count limit
- critical_gaps total limit is 5 (all severities)

---

### Subtask T006 – Unit Tests for Pydantic Validators
- **Purpose**: Verify all validators work correctly
- **Steps**:
  1. Create `tests/test_enhanced_conclusion/test_types.py`
  2. Test EvidenceReference:
     - Valid reference with all fields
     - Quote > 200 chars (verify truncation)
     - Missing required fields (should fail)
  3. Test RoleAnalysis:
     - 3 strengths, 3 weaknesses (should pass)
     - 6 strengths (should fail with clear error)
     - Empty strengths/weaknesses (should pass)
  4. Test Verdict:
     - 120 words (should pass)
     - 150 words (should pass)
     - 119 words (should fail)
     - 151 words (should fail)
     - Invalid confidence (should fail)
  5. Test CriticalGap:
     - Valid gap with all fields
     - Empty sources list (should fail)
     - Empty evidence list (should fail)
  6. Test Recommendation:
     - Valid recommendation with all fields
     - Missing source_evidence (should fail)
  7. Test EnhancedConclusion:
     - 5 critical gaps (should pass)
     - 6 critical gaps (should fail)
     - 5 high-priority recommendations (should pass)
     - 6 high-priority recommendations (should fail)

**Files**:
- `tests/test_enhanced_conclusion/test_types.py` (new file, ~200 lines)

**Parallel?**: Yes (can be developed alongside other subtasks)

**Notes**:
- Use pytest for test framework
- Use pytest.raises for validation error tests
- Include Russian text in some tests to verify UTF-8

---

## Test Strategy

**Test Location**: `tests/test_enhanced_conclusion/test_types.py`

**Test Commands**:
```bash
# Run all type tests
pytest tests/test_enhanced_conclusion/test_types.py -v

# Run specific test
pytest tests/test_enhanced_conclusion/test_types.py::test_evidence_reference_truncation -v

# Run with coverage
pytest tests/test_enhanced_conclusion/test_types.py --cov=src/types/enhanced_conclusion_types
```

**Fixtures Needed**:
- Valid evidence reference object
- Valid role analysis object
- Valid verdict object
- Sample text > 200 chars for truncation test
- Sample text with 119, 120, 150, 151 words for word count test

**Coverage Target**: > 95% (all validators tested)

---

## Risks & Mitigations

**Risk 1**: Pydantic v2 syntax errors
- **Mitigation**: Use pydantic v2 documentation as reference, test each model immediately

**Risk 2**: Word count validator too strict (doesn't handle hyphens, apostrophes)
- **Mitigation**: Simple split() is acceptable for MVP; can enhance later if needed

**Risk 3**: UTF-8 encoding issues with Russian text
- **Mitigation**: Include Russian text in tests, verify no encoding errors

**Risk 4**: Validator error messages unclear
- **Mitigation**: Write descriptive error messages in all validators

---

## Review Guidance

**Key Acceptance Checkpoints**:
1. All Pydantic models defined with correct field types and constraints
2. EvidenceReference auto-truncates quotes to 200 chars
3. RoleAnalysis enforces 3-5 bullet limit
4. Verdict enforces 120-150 word limit
5. EnhancedConclusion enforces max 5 gaps and max 5 high-priority recommendations
6. Unit tests pass with > 95% coverage
7. Russian text works without encoding errors

**Review Before Approval**:
- Check all validators raise clear ValidationError messages
- Verify quote truncation actually works (test with >200 char string)
- Verify word count validator works (test with 119, 120, 150, 151 words)
- Verify duplicate role names are rejected
- Verify max limits are enforced (6 items should fail)

---

## Activity Log

> **CRITICAL**: Activity log entries MUST be in chronological order (oldest first, newest last).

### How to Add Activity Log Entries

**When adding an entry**:
1. Scroll to the bottom of this file (Activity Log section below "Valid lanes")
2. **APPEND the new entry at the END** (do NOT prepend or insert in middle)
3. Use exact format: `- YYYY-MM-DDTHH:MM:SSZ – agent_id – lane=<lane> – <action>`
4. Timestamp MUST be current time in UTC (check with `date -u "+%Y-%m-%dT%H:%M:%SZ"`)
5. Lane MUST match the frontmatter `lane:` field exactly
6. Agent ID should identify who made the change (claude-sonnet-4-5, codex, etc.)

**Format**:
```
- YYYY-MM-DDTHH:MM:SSZ – <agent_id> – lane=<lane> – <brief action description>
```

**Example (correct chronological order)**:
```
- 2026-01-12T10:00:00Z – system – lane=planned – Prompt created
- 2026-01-12T10:30:00Z – claude – lane=doing – Started implementation
- 2026-01-12T11:00:00Z – codex – lane=for_review – Implementation complete, ready for review
- 2026-01-12T11:30:00Z – claude – lane=done – Review passed, all tests passing  ← LATEST (at bottom)
```

**Common mistakes (DO NOT DO THIS)**:
- ❌ Adding new entry at the top (breaks chronological order)
- ❌ Using future timestamps (causes acceptance validation to fail)
- ❌ Lane mismatch: frontmatter says `lane: "done"` but log entry says `lane=doing`
- ❌ Inserting in middle instead of appending to end

**Why this matters**: The acceptance system reads the LAST activity log entry as the current state. If entries are out of order, acceptance will fail even when the work is complete.

**Initial entry**:
- 2025-02-16T12:00:00Z – system – lane=planned – Prompt created.

---

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter AND append activity log entry (at the end)
2. **Use CLI**: `spec-kitty agent tasks move-task <WPID> --to <lane> --note "message"` (recommended)

The CLI command updates both frontmatter and activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`

### Optional Phase Subdirectories

For large features, organize prompts under `tasks/` to keep bundles grouped while maintaining lexical ordering.
- 2026-02-15T22:27:55Z – claude-sonnet-4-5 – shell_pid=71233 – lane=doing – Assigned agent via workflow command
- 2026-02-15T22:31:15Z – claude-sonnet-4-5 – shell_pid=71233 – lane=for_review – Ready for review: Implemented all Pydantic types with FR-031, FR-030, FR-029 compliance. 38 unit tests passing. EvidenceReference with auto-truncation, RoleAnalysis with 3-5 bullet limit, Verdict with 120-150 word limit, EnhancedConclusion with max 5 gaps and 5 high-priority recommendations. UTF-8 support for Russian/English.
- 2026-02-15T23:39:19Z – claude – shell_pid=84523 – lane=doing – Started review via workflow command
- 2026-02-15T23:39:49Z – claude – shell_pid=84523 – lane=done – Review passed: All 38 tests passing. Full FR-029, FR-030, FR-031 compliance. EvidenceReference with auto-truncation, RoleAnalysis with 3-5 bullet limit, Verdict with 120-150 word limit, EnhancedConclusion with max 5 gaps and 5 high-priority recommendations.
