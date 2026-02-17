---
work_package_id: WP06
title: Stage 2 - Gap & Recommendation Generator
lane: "done"
dependencies: []
base_branch: main
base_commit: 9d5705de96b438c1c93f45e8d9bcaad029b92cfe
created_at: '2026-02-15T23:20:32.743100+00:00'
subtasks:
- T029
- T030
- T031
- T032
- T033
- T034
phase: Phase 1 - Core Pipeline
assignee: ''
agent: "claude"
shell_pid: "80973"
review_status: "approved"
reviewed_by: "ALeks ishmanov"
history:
- timestamp: '2025-02-16T12:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt generated via /spec-kitty.tasks
---

# Work Package Prompt: WP06 – Stage 2 - Gap & Recommendation Generator

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_status` field above. If it says `has_feedback`, scroll to the **Review Feedback** section immediately.

---

## Objectives & Success Criteria

**Objectives**:
1. Implement gap identification from intermediate schema
2. Implement recommendation generation with problem→action→metric format
3. Rank gaps by severity (number of sources, argument strength, judge emphasis)
4. Prioritize recommendations (High/Medium/Low)
5. Enforce max 5 gaps and max 5 high-priority recommendations

**Success Criteria**:
- Gaps identified from cross-role weaknesses
- Gaps ranked by severity correctly
- Recommendations follow problem→action→metric format
- Max 5 critical gaps enforced
- Max 5 high-priority recommendations enforced
- All recommendations traceable to evidence

---

## Context & Constraints

**Supporting Documents**:
- Spec: `kitty-specs/011-enhanced-committee-debate-conclusion/spec.md` (FR-010 to FR-017, FR-026, FR-027)
- Data Model: `kitty-specs/011-enhanced-committee-debate-conclusion/data-model.md` (CriticalGap, Recommendation)
- Plan: `kitty-specs/011-enhanced-committee-debate-conclusion/plan.md` (Stage 2 design)

**Dependencies**:
- WP01: Pydantic types (CriticalGap, Recommendation, IntermediateConclusionSchema)
- WP02: Analyzer base class
- WP03: Verdict extractor (provides verdict input)
- WP04: Role analyzer (provides role analyses input)
- WP05: Confidence calculator (provides confidence context)

**Constraints**:
- Must use IntermediateConclusionSchema as input (Stage 1 output)
- Must NOT generate generic recommendations (FR-026, FR-027)
- Must enforce max 5 gaps (FR-030)
- Must enforce max 5 high-priority recommendations (FR-030)
- Performance target: < 5 seconds

---

## Subtasks & Detailed Guidance

### T029: Create GapRecommendationGenerator Class
- Create `src/analyzers/gap_recommendation_generator.py`
- Extend EnhancedAnalyzer
- Implement __call__ taking IntermediateConclusionSchema
- Return Tuple[List[CriticalGap], List[Recommendation]]

### T030: Implement _identify_critical_gaps()
- Analyze weaknesses across all RoleAnalysis objects
- Look for patterns (same weakness mentioned by multiple roles)
- Rank by severity: number of sources × argument strength × judge emphasis
- Return top 5 gaps max

### T031: Implement _generate_recommendations()
- Generate recommendations from identified gaps
- Format: problem → action → metric (FR-014)
- Assign priority based on gap severity
- Ensure each recommendation has source_evidence
- Limit high-priority to 5 max

### T032: Implement _rank_gaps_by_severity()
- Count number of roles who mentioned each gap
- Weight by argument strength (High=3, Medium=2, Low=1)
- Weight by judge emphasis (mentioned in verdict = 2x)
- Sort by severity score descending

### T033: Create gap_recommendation_prompt.md
- Create `src/prompts/enhanced_conclusion/gap_recommendation_prompt.md`
- Input: IntermediateConclusionSchema (verdict + role_analyses)
- Output: CriticalGap[] + Recommendation[]
- Emphasize evidence grounding (FR-026, FR-027)
- Specify max limits (5 gaps, 5 high-priority recommendations)

### T034: Unit Tests
- Test gap identification from role analyses
- Test severity ranking logic
- Test recommendation format (problem→action→metric)
- Test max limits enforcement
- Test evidence traceability

---

## Files

- `src/analyzers/gap_recommendation_generator.py` (new file, ~250 lines)
- `src/prompts/enhanced_conclusion/gap_recommendation_prompt.md` (new file, ~100 lines)
- `tests/test_enhanced_conclusion/test_gap_recommendation_generator.py` (new file, ~200 lines)

---

## Test Strategy

**Test Location**: `tests/test_enhanced_conclusion/test_gap_recommendation_generator.py`

**Test Commands**:
```bash
pytest tests/test_enhanced_conclusion/test_gap_recommendation_generator.py -v
```

**Fixtures Needed**:
- Sample IntermediateConclusionSchema with multiple role analyses
- Mock LLM response with gaps and recommendations

---

## Risks & Mitigations

**Risk 1**: Generic recommendations generated
- **Mitigation**: Prompt emphasizes evidence grounding, validate in tests

**Risk 2**: Gap ranking too simplistic
- **Mitigation**: Weight by multiple factors (sources, strength, judge emphasis)

**Risk 3**: Recommendations exceed max limits
- **Mitigation**: Slice to max 5 in code, Pydantic validator enforces

---

## Review Guidance

**Key Acceptance Checkpoints**:
1. Gaps identified from cross-role patterns
2. Severity ranking considers multiple factors
3. Recommendations follow problem→action→metric format exactly
4. Max 5 gaps enforced
5. Max 5 high-priority recommendations enforced
6. All recommendations traceable to evidence
7. No generic "best practices" recommendations

---

## Activity Log

- 2025-02-16T12:00:00Z – system – lane=planned – Prompt created.
- 2026-02-15T23:20:32Z – claude – shell_pid=80973 – lane=doing – Assigned agent via workflow command
- 2026-02-15T23:24:44Z – claude – shell_pid=80973 – lane=for_review – Ready for review: Gap & Recommendation Generator implemented with problem→action→metric format, 22 unit tests passing
- 2026-02-15T23:41:03Z – claude – shell_pid=80973 – lane=done – Review passed: 22/22 tests passing
