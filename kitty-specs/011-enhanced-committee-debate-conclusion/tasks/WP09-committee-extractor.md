---
work_package_id: WP09
title: Committee Debate Final Report Extractor
lane: "done"
dependencies: []
base_branch: main
base_commit: 9d5705de96b438c1c93f45e8d9bcaad029b92cfe
created_at: '2026-02-15T23:59:26.439067+00:00'
subtasks:
- T046
- T047
- T048
- T049
- T050
phase: Phase 1 - Data Extraction
assignee: ''
agent: "claude"
shell_pid: "95767"
review_status: "approved"
reviewed_by: "ALeks ishmanov"
history:
- timestamp: '2025-02-16T12:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt generated via /spec-kitty.tasks
---

# Work Package Prompt: WP09 – Committee Debate Final Report Extractor

## Objectives & Success Criteria

**Objectives**:
1. Create extractor for parsing committee debate final_report.md
2. Parse room sections (TPM vs CPO, TPM vs CFO, etc.)
3. Extract room outcomes (winner/loser)
4. Extract judge rationales
5. Extract transcript data with turn indices

**Success Criteria**:
- final_report.md parsed correctly
- All rooms identified
- Winners extracted from each room
- Judge rationales extracted
- Transcript data accessible for evidence extraction

---

## Context & Constraints

**Supporting Documents**:
- Spec: `kitty-specs/011-enhanced-committee-debate-conclusion/spec.md` (WF-001: single source of truth)

**Dependencies**:
- None (can run in parallel with WP01, WP02)

**Constraints**:
- Must handle varying final_report.md formats
- Must support both Russian and English

---

## Subtasks

### T046: Create CommitteeReportExtractor class
- Create `src/extractors/committee_report_extractor.py`
- Implement parse(final_report_path) method
- Return CommitteeReportData structure

### T047: Implement _parse_room_sections()
- Identify each debate room section
- Extract room names (TPM_vs_CPO, etc.)
- Handle varying header formats

### T048: Implement _extract_room_outcomes()
- Extract winner from each room
- Handle "Winner:", "Verdict:", and other formats
- Return dict mapping room_id to winner

### T049: Implement _extract_transcript_data()
- Extract transcript with turn indices
- Return structured data for evidence extraction
- Handle missing or incomplete transcripts

### T050: Unit tests
- Test with sample final_report.md
- Test room parsing
- Test outcome extraction
- Test transcript extraction

---

## Files

- `src/extractors/committee_report_extractor.py` (new file, ~150 lines)
- `tests/test_enhanced_conclusion/test_committee_extractor.py` (new file, ~120 lines)

---

## Activity Log

- 2025-02-16T12:00:00Z – system – lane=planned – Prompt created.
- 2026-02-15T23:59:26Z – claude – shell_pid=89156 – lane=doing – Assigned agent via workflow command
- 2026-02-16T00:02:51Z – claude – shell_pid=89156 – lane=for_review – Ready for review: Committee Report Extractor complete with all 5 subtasks (T046-T050) implemented and tested. 19/19 unit tests passing.
- 2026-02-16T00:19:56Z – claude – shell_pid=95767 – lane=doing – Started review via workflow command
- 2026-02-16T00:20:21Z – claude – shell_pid=95767 – lane=done – Review passed: All 19/19 tests passing, requirements met, UTF-8 encoding support verified, clean data structures
