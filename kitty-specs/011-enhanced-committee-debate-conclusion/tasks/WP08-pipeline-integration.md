---
work_package_id: WP08
title: Pipeline Integration in ConclusionReportNode
lane: "done"
dependencies: []
base_branch: main
base_commit: 9d5705de96b438c1c93f45e8d9bcaad029b92cfe
created_at: '2026-02-15T23:25:53.346980+00:00'
subtasks:
- T041
- T042
- T043
- T044
- T045
phase: Phase 1 - Integration
assignee: ''
agent: "claude"
shell_pid: "95432"
review_status: "approved"
reviewed_by: "ALeks ishmanov"
history:
- timestamp: '2025-02-16T12:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt generated via /spec-kitty.tasks
---

# Work Package Prompt: WP08 – Pipeline Integration in ConclusionReportNode

## Objectives & Success Criteria

**Objectives**:
1. Integrate enhanced pipeline into ConclusionReportNode
2. Route committee debates to enhanced pipeline
3. Route standard/document debates to existing pipeline
4. Write to committee_output/{run_id}/conclusion.md
5. Handle errors gracefully

**Success Criteria**:
- Committee debates use enhanced pipeline
- Standard/document debates use existing pipeline (unchanged)
- Enhanced conclusion.md written to correct location
- Fallback to basic conclusion if enhanced fails
- End-to-end integration test passes

---

## Context & Constraints

**Supporting Documents**:
- Spec: `kitty-specs/011-enhanced-committee-debate-conclusion/spec.md` (WF-001 to WF-006)
- Plan: `kitty-specs/011-enhanced-committee-debate-conclusion/plan.md` (integration design)

**Dependencies**:
- WP03: Verdict Extractor
- WP04: Role Analyzer
- WP06: Gap & Recommendation Generator
- WP07: Enhanced Conclusion Writer

**Constraints**:
- Must NOT break existing standard/document debate flows
- Performance target: < 10 seconds total (FR-028)
- Must handle errors gracefully

---

## Subtasks

### T041: Update ConclusionReportNode to detect committee debates
- Modify __call__ to check debate type
- Route committee debates to enhanced pipeline
- Route others to existing pipeline

### T042: Implement _run_enhanced_pipeline()
- Read final_report.md from committee_output/{run_id}/
- Run Stage 1A: VerdictExtractor
- Run Stage 1B: RoleAnalyzer
- Build IntermediateConclusionSchema
- Run Stage 2: GapRecommendationGenerator
- Build EnhancedConclusion
- Write using EnhancedConclusionWriter

### T043: Add final_report.md reading logic
- Locate final_report.md in committee_output/{run_id}/
- Read with UTF-8 encoding
- Handle missing file gracefully

### T044: Update output path to committee_output/{run_id}/conclusion.md
- Extract run_id from state
- Write enhanced conclusion to correct location
- Verify file written successfully

### T045: Integration test
- Create test with mock final_report.md
- Verify complete pipeline execution
- Verify output file location
- Verify all sections present

---

## Files

- `src/nodes/conclusion_report_node.py` (modify, ~100 lines added)
- `tests/test_enhanced_conclusion/test_pipeline_integration.py` (new file, ~180 lines)

---

## Activity Log

- 2025-02-16T12:00:00Z – system – lane=planned – Prompt created.
- 2026-02-15T23:25:53Z – claude – shell_pid=83472 – lane=doing – Assigned agent via workflow command
- 2026-02-15T23:58:57Z – claude – shell_pid=83472 – lane=for_review – Ready for review: Enhanced pipeline integration complete with all 5 subtasks (T041-T045) implemented and tested. 14/14 integration tests passing.
- 2026-02-16T00:19:06Z – claude – shell_pid=95432 – lane=doing – Started review via workflow command
- 2026-02-16T00:19:54Z – claude – shell_pid=95432 – lane=done – Review passed: All 14/14 tests passing, requirements met, backward compatibility maintained, clean architecture
