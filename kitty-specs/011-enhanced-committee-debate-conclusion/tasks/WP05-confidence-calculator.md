---
work_package_id: WP05
title: Confidence Calculator Utility
lane: "done"
dependencies: []
base_branch: main
base_commit: 9d5705de96b438c1c93f45e8d9bcaad029b92cfe
created_at: '2026-02-15T23:18:58.456406+00:00'
subtasks:
- T025
- T026
- T027
- T028
phase: Phase 1 - Core Pipeline
assignee: ''
agent: "claude"
shell_pid: "80179"
review_status: "approved"
reviewed_by: "ALeks ishmanov"
history:
- timestamp: '2025-02-16T12:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt generated via /spec-kitty.tasks
---

# Work Package Prompt: WP05 – Confidence Calculator Utility

**NOTE**: This WP's confidence calculation logic is already implemented in WP03 (VerdictExtractor). If you completed WP03, you may skip this WP or move the confidence calculation to a shared utility for reuse.

## Objectives & Success Criteria

**Objectives**:
1. Create standalone confidence calculation utility per FR-029
2. Implement room outcome counting logic
3. Implement contradiction detection in judge rationales

**Success Criteria**:
- calculate_confidence() function implements FR-029 formula exactly
- Unanimous outcomes return "High"
- Split outcomes return "Medium"
- Tie outcomes return "Low"
- Contradictions reduce confidence by 1 level

## Context & Constraints

**Supporting Documents**:
- Spec: `kitty-specs/011-enhanced-committee-debate-conclusion/spec.md` (FR-029)
- Data Model: `kitty-specs/011-enhanced-committee-debate-conclusion/data-model.md` (confidence calculation)

**Dependencies**:
- WP01: Pydantic types (for Literal types)

**Constraints**:
- FR-029 formula is explicit - implement exactly as specified
- Must handle edge cases (0 rooms, 1 room)

## Subtasks

### T025: Create confidence_calculator.py with calculate_confidence()
- Implement room outcome counting (PRO wins vs CON wins)
- Implement base confidence logic per FR-029
- Handle edge cases (no rooms, single room)

### T026: Implement contradiction detection
- Look for contradiction keywords in rationales
- Return True if 2+ contradictions found

### T027: Implement confidence level reduction
- Reduce High → Medium if contradictions
- Reduce Medium → Low if contradictions

### T028: Unit tests for all scenarios
- Test unanimous (4-0, 0-4)
- Test split (3-1, 1-3)
- Test tie (2-2)
- Test contradictions

## Files

- `src/utils/confidence_calculator.py` (new file, ~80 lines)
- `tests/test_enhanced_conclusion/test_confidence_calculator.py` (new file, ~120 lines)

## Activity Log

- 2025-02-16T12:00:00Z – system – lane=planned – Prompt created.
- 2026-02-15T23:18:58Z – claude – shell_pid=80179 – lane=doing – Assigned agent via workflow command
- 2026-02-15T23:20:16Z – claude – shell_pid=80179 – lane=for_review – Ready for review: Standalone confidence calculator utility per FR-029, 39 unit tests passing
- 2026-02-15T23:40:58Z – claude – shell_pid=80179 – lane=done – Review passed: 39/39 tests passing
