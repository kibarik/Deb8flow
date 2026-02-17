---
work_package_id: WP07
title: Enhanced Conclusion Writer
lane: "done"
dependencies: []
base_branch: main
base_commit: 9d5705de96b438c1c93f45e8d9bcaad029b92cfe
created_at: '2026-02-15T23:25:01.805998+00:00'
subtasks:
- T035
- T036
- T037
- T038
- T039
- T040
phase: Phase 1 - Core Pipeline
assignee: ''
agent: "claude"
shell_pid: "82997"
review_status: "approved"
reviewed_by: "ALeks ishmanov"
history:
- timestamp: '2025-02-16T12:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt generated via /spec-kitty.tasks
---

# Work Package Prompt: WP07 – Enhanced Conclusion Writer

## Objectives & Success Criteria

**Objectives**:
1. Create markdown writer for enhanced conclusion format
2. Format all sections per spec structure
3. Format evidence references correctly
4. Handle empty lists gracefully
5. Support UTF-8 encoding for Russian/English

**Success Criteria**:
- EnhancedConclusionWriter writes complete markdown
- All sections present and correctly formatted
- Evidence references formatted as [room_id, speaker_role, turn_index, "quote"]
- UTF-8 encoding works for Russian text
- Empty lists handled (no gaps, no recommendations)

---

## Context & Constraints

**Supporting Documents**:
- Spec: `kitty-specs/011-enhanced-committee-debate-conclusion/spec.md` (Output Structure section)
- Data Model: `kitty-specs/011-enhanced-committee-debate-conclusion/data-model.md` (EnhancedConclusion)

**Dependencies**:
- WP01: Pydantic types (EnhancedConclusion model)
- WP06: Gap & Recommendation Generator (provides complete EnhancedConclusion)

**Constraints**:
- Must match spec output structure exactly
- Must handle UTF-8 for Russian/English
- Must handle empty lists gracefully

---

## Subtasks

### T035: Create EnhancedConclusionWriter class
- Create `src/utils/enhanced_conclusion_writer.py`
- Implement write(enhanced_conclusion, output_path) method
- Use UTF-8 encoding

### T036: Implement _format_verdict_section()
- Format with Answer, Confidence, Rationale, Room Outcomes
- Enforce 120-150 word display (truncate if needed)

### T037: Implement _format_role_analysis_section()
- Format each role with Strengths and Weaknesses
- Display 3-5 bullets each
- Format evidence references

### T038: Implement _format_gaps_section() and _format_recommendations_section()
- Format Critical Gaps (max 5) with severity
- Format Action Plan with High/Medium/Low subsections
- Format problem→action→metric recommendations

### T039: Implement _format_evidence_reference()
- Format as: [room_id, speaker_role, turn_index, "quote..."]
- Truncate quote to 200 chars for display

### T040: Unit tests
- Test markdown format matches spec
- Test evidence reference formatting
- Test empty list handling
- Test UTF-8 encoding with Russian text

---

## Files

- `src/utils/enhanced_conclusion_writer.py` (new file, ~200 lines)
- `tests/test_enhanced_conclusion/test_enhanced_writer.py` (new file, ~150 lines)

---

## Activity Log

- 2025-02-16T12:00:00Z – system – lane=planned – Prompt created.
- 2026-02-15T23:25:01Z – claude – shell_pid=82997 – lane=doing – Assigned agent via workflow command
- 2026-02-15T23:25:45Z – claude – shell_pid=82997 – lane=for_review – Ready for review: Enhanced Conclusion Writer with markdown formatting and UTF-8 support, 6 tests passing
- 2026-02-15T23:41:08Z – claude – shell_pid=82997 – lane=done – Review passed: 6/6 tests passing
