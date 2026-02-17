# Work Packages: Enhanced Committee Debate Conclusion Report

**Feature**: 011-enhanced-committee-debate-conclusion
**Generated**: 2025-02-16
**Total Work Packages**: 11
**Total Subtasks**: 48

---

## Work Package Overview

| WP | Title | Priority | Subtasks | Prompt Size | Dependencies |
|----|-------|----------|----------|-------------|--------------|
| WP01 | Foundation: Pydantic Types | P1 | 5 | ~300 lines | None |
| WP02 | Foundation: Analyzer Base | P1 | 4 | ~250 lines | WP01 |
| WP03 | Stage 1A: Verdict Extraction | P1 | 5 | ~350 lines | WP02 |
| WP04 | Stage 1B: Role Analysis | P1 | 6 | ~400 lines | WP02 |
| WP05 | Confidence Calculator | P1 | 4 | ~280 lines | WP01 |
| WP06 | Stage 2: Gap & Recommendation Generator | P1 | 6 | ~420 lines | WP03, WP04, WP05 |
| WP07 | Enhanced Conclusion Writer | P1 | 5 | ~350 lines | WP01, WP06 |
| WP08 | Pipeline Integration | P1 | 4 | ~320 lines | WP03, WP04, WP06, WP07 |
| WP09 | Committee Debate Extractor | P1 | 4 | ~300 lines | None |
| WP10 | Length & Evidence Validation | P1 | 5 | ~380 lines | WP01, WP03, WP04, WP06 |
| WP11 | Integration & E2E Testing | P1 | 4 | ~340 lines | WP08, WP09, WP10 |

**Size Distribution**: All WPs within ideal range (4-6 subtasks, ~280-420 lines each)
**Parallelization**: WP01, WP02, WP09 can run in parallel; WP03-WP05 can run in parallel after WP02
**MVP Scope**: WP01-WP08 (core enhanced conclusion pipeline)

---

## WP01: Foundation - Pydantic Types for Enhanced Conclusion

**Goal**: Create Pydantic models for the enhanced conclusion pipeline with validation for evidence references, length limits, and structured data.

**Priority**: P1 (Foundational - blocks all other WPs)

**Independent Test**: Create test file that instantiates each Pydantic model with valid data and verifies all validators work (quote truncation, length limits, etc.).

**Included Subtasks**:
- [x] T001: Create `src/types/enhanced_conclusion_types.py` with EvidenceReference model (FR-031 compliance)
- [x] T002: Add Strength, Weakness, RoleAnalysis models with 3-5 bullet validation (FR-030)
- [x] T003: Add Verdict, IntermediateConclusionSchema models with word count validation
- [x] T004: Add CriticalGap, Recommendation models with severity/priority enums
- [x] T005: Add EnhancedConclusion model with max 5 gaps and max 5 high-priority recommendations validation
- [x] T006: [P] Create unit tests for all Pydantic validators in `tests/test_enhanced_conclusion/test_types.py`

**Implementation Sketch**:
1. Create new file `src/types/enhanced_conclusion_types.py`
2. Import pydantic BaseModel, Field, field_validator, Literal
3. Implement EvidenceReference with room_id, speaker_role, turn_index, quote (max 200 chars)
4. Implement Strength/Weakness with description and EvidenceReference
5. Implement RoleAnalysis with strengths/weaknesses lists (3-5 max via validator)
6. Implement Verdict with answer (120-150 words), confidence (High/Medium/Low), rationale
7. Implement CriticalGap with title, severity, description, sources[], evidence[]
8. Implement Recommendation with priority, problem, action, metric, source_evidence
9. Implement EnhancedConclusion as aggregate model
10. Write unit tests for each validator (quote truncation, length limits, max counts)

**Parallel Opportunities**: None (foundational)

**Dependencies**: None

**Risks**:
- Pydantic version compatibility (project uses pydantic v2)
- Validators must not break on valid data

**Estimated Prompt Size**: ~300 lines

---

## WP02: Foundation - Analyzer Base & Pipeline Utilities

**Goal**: Create base analyzer class and pipeline utilities for the two-stage enhanced conclusion architecture.

**Priority**: P1 (Foundational - enables Stage 1 & Stage 2 analyzers)

**Independent Test**: Create a dummy analyzer that inherits from base class and verify it can be instantiated and called with test input.

**Included Subtasks**:
- [x] T007: Create `src/analyzers/__init__.py` and base_analyzer.py with EnhancedAnalyzer base class
- [x] T008: Add LLM chain creation methods in base class (structured/unstructured output support)
- [x] T009: Add prompt loading utility for loading markdown prompts from `src/prompts/enhanced_conclusion/`
- [x] T010: Add retry logic with exponential backoff for LLM calls
- [x] T011: [P] Create unit tests for base analyzer in `tests/test_enhanced_conclusion/test_base_analyzer.py`

**Implementation Sketch**:
1. Create `src/analyzers/` directory
2. Create `base_analyzer.py` with EnhancedAnalyzer class inheriting from BaseComponent
3. Implement `__init__` with llm_config parameter
4. Implement `_create_structured_chain()` method for Pydantic output
5. Implement `_create_text_chain()` method for raw text output
6. Implement `_load_prompt()` method to read from prompts directory
7. Add retry decorator with 3 attempts, exponential backoff
8. Write tests for chain creation and retry logic

**Parallel Opportunities**: None (foundational)

**Dependencies**: None

**Risks**:
- Must align with existing BaseComponent pattern
- Retry logic must not cause excessive delays

**Estimated Prompt Size**: ~250 lines

---

## WP03: Stage 1A - Verdict Extractor with Confidence Calculation

**Goal**: Implement verdict extraction from final_report.md with confidence level calculation per FR-029 formula.

**Priority**: P1 (Core feature - User Story 1)

**Independent Test**: Run verdict extractor on sample final_report.md and verify it extracts verdict with correct confidence level (unanimous=High, split=Medium, tie=Low).

**Included Subtasks**:
- [x] T012: Create `src/analyzers/verdict_extractor.py` with VerdictExtractor class
- [x] T013: Implement `_extract_room_outcomes()` to parse winner from each room in final_report.md
- [x] T014: Implement `_calculate_confidence()` with FR-029 formula (unanimous=High, 3-1=Medium, 2-2=Low, contradictions reduce by 1)
- [x] T015: Implement `_detect_contradictions()` to identify conflicting judge rationales
- [x] T016: Create `src/prompts/enhanced_conclusion/verdict_extraction_prompt.md` for verdict extraction
- [x] T017: [P] Create unit tests in `tests/test_enhanced_conclusion/test_verdict_extractor.py`

**Implementation Sketch**:
1. Create VerdictExtractor extending EnhancedAnalyzer
2. Implement `__call__(final_report_text: str) -> Verdict`
3. Parse final_report.md to extract room outcomes (TPM vs CPO: CON won, etc.)
4. Extract judge rationales from each room
5. Calculate confidence using FR-029 formula:
   - Count PRO/CON wins across rooms
   - Unanimous (4-0 or 0-4) = High
   - Split (3-1 or 1-3) = Medium
   - Tie (2-2) = Low
   - Reduce by 1 level if contradictions detected
6. Create prompt template for extracting verdict answer text
7. Write tests for confidence calculation edge cases

**Parallel Opportunities**: Can run in parallel with WP04 (both Stage 1)

**Dependencies**: WP02

**Risks**:
- final_report.md format may vary
- Contradiction detection may have false positives
- Must handle edge cases (no rooms, single room, missing data)

**Estimated Prompt Size**: ~350 lines

---

## WP04: Stage 1B - Role Analyzer with Evidence Extraction

**Goal**: Implement role-based analysis extraction (strengths/weaknesses) with evidence references per FR-031.

**Priority**: P1 (Core feature - User Story 1)

**Independent Test**: Run role analyzer on sample final_report.md and verify it extracts 3-5 strengths/weaknesses per role with complete evidence references (room_id, speaker_role, turn_index, quote).

**Included Subtasks**:
- [x] T018: Create `src/analyzers/role_analyzer.py` with RoleAnalyzer class
- [x] T019: Implement `_extract_role_mentions()` to identify all role appearances in final_report.md
- [x] T020: Implement `_extract_strengths()` with 3-5 bullet limit and evidence references
- [x] T021: Implement `_extract_weaknesses()` with 3-5 bullet limit and evidence references
- [x] T022: Implement `_extract_evidence_reference()` to parse room_id, speaker_role, turn_index, quote (max 200 chars)
- [x] T023: Create `src/prompts/enhanced_conclusion/role_analysis_prompt.md` for role analysis
- [x] T024: [P] Create unit tests in `tests/test_enhanced_conclusion/test_role_analyzer.py`

**Implementation Sketch**:
1. Create RoleAnalyzer extending EnhancedAnalyzer
2. Implement `__call__(final_report_text: str) -> List[RoleAnalysis]`
3. Parse final_report.md to identify all participating roles (TPM, CPO, CFO, CTO, BDM)
4. For each role:
   - Extract strengths (3-5 max) with supporting evidence
   - Extract weaknesses (3-5 max) with supporting evidence
   - Each strength/weakness must have EvidenceReference with:
     - room_id (e.g., "TPM_vs_CPO")
     - speaker_role (e.g., "CPO")
     - turn_index (integer from transcript)
     - quote (truncated to 200 chars)
5. Create prompt template for structured role analysis
6. Write tests for evidence extraction completeness

**Parallel Opportunities**: Can run in parallel with WP03 (both Stage 1)

**Dependencies**: WP02

**Risks**:
- Role names may vary across rooms
- Evidence extraction may fail if transcript format is inconsistent
- Must handle roles that appear in some rooms but not others

**Estimated Prompt Size**: ~400 lines

---

## WP05: Confidence Calculator Utility

**Goal**: Implement standalone confidence calculation utility per FR-029 with contradiction detection.

**Priority**: P1 (Core feature - FR-029 compliance)

**Independent Test**: Test confidence calculator with various room outcomes (4-0, 3-1, 2-2) and verify correct confidence levels.

**Included Subtasks**:
- [x] T025: Create `src/utils/confidence_calculator.py` with calculate_confidence() function
- [x] T026: Implement room outcome counting logic (PRO wins vs CON wins)
- [x] T027: Implement contradiction detection in judge rationales
- [x] T028: [P] Create unit tests in `tests/test_enhanced_conclusion/test_confidence_calculator.py`

**Implementation Sketch**:
1. Create `confidence_calculator.py`
2. Implement `calculate_confidence(room_outcomes: dict, judge_rationales: list[str]) -> str`
3. Count wins: tpm_wins = sum(1 for winner in room_outcomes.values() if winner == "PRO")
4. Base confidence logic:
   - If total_rooms == 0: return "Low"
   - If tpm_wins == total_rooms or tpm_wins == 0: return "High"
   - If abs(tpm_wins - total_rooms/2) <= 0.5: return "Low"
   - Else: return "Medium"
5. Contradiction detection:
   - Look for keywords: "however", "contradicts", "inconsistent", "conflicting"
   - If >= 2 contradictions found, reduce confidence by 1 level
6. Write tests for all confidence scenarios

**Parallel Opportunities**: Can run in parallel with WP03, WP04

**Dependencies**: WP01 (for Literal types)

**Risks**:
- Contradiction detection may be too simplistic
- Edge cases (0 rooms, 1 room) need careful handling

**Estimated Prompt Size**: ~280 lines

---

## WP06: Stage 2 - Gap & Recommendation Generator

**Goal**: Implement synthesis stage that processes intermediate schema to generate critical gaps and prioritized recommendations.

**Priority**: P1 (Core feature - User Story 1 & 3)

**Independent Test**: Run gap/recommendation generator on sample intermediate schema and verify it produces max 5 gaps and max 5 high-priority recommendations with problem→action→metric format.

**Included Subtasks**:
- [x] T029: Create `src/analyzers/gap_recommendation_generator.py` with GapRecommendationGenerator class
- [x] T030: Implement `_identify_critical_gaps()` with cross-role pattern matching and severity ranking
- [x] T031: Implement `_generate_recommendations()` with problem→action→metric format and priority assignment
- [x] T032: Implement `_rank_gaps_by_severity()` considering number of sources, argument strength, judge emphasis
- [x] T033: Create `src/prompts/enhanced_conclusion/gap_recommendation_prompt.md` for synthesis
- [x] T034: [P] Create unit tests in `tests/test_enhanced_conclusion/test_gap_recommendation_generator.py`

**Implementation Sketch**:
1. Create GapRecommendationGenerator extending EnhancedAnalyzer
2. Implement `__call__(intermediate_schema: IntermediateConclusionSchema) -> Tuple[List[CriticalGap], List[Recommendation]]`
3. Input: Verdict + RoleAnalysis[] from Stage 1
4. Identify critical gaps:
   - Look for weaknesses mentioned by multiple roles
   - Rank by severity (number of sources × strength × judge emphasis)
   - Max 5 gaps total
   - Each gap needs: title, severity, description, sources[], evidence[]
5. Generate recommendations:
   - Each recommendation: problem → action → metric
   - Prioritize: High/Medium/Low
   - Max 5 high-priority recommendations
   - Each recommendation needs: priority, problem, action, metric, source_evidence
6. Create synthesis prompt template
7. Write tests for gap ranking and recommendation format

**Parallel Opportunities**: None (depends on Stage 1 outputs)

**Dependencies**: WP03, WP04, WP05

**Risks**:
- Gap identification may miss cross-role patterns
- Recommendations may be generic if not grounded in evidence
- Must enforce max 5 limits for gaps and high-priority recommendations

**Estimated Prompt Size**: ~420 lines

---

## WP07: Enhanced Conclusion Writer

**Goal**: Implement markdown writer for enhanced conclusion format with proper section ordering and evidence reference formatting.

**Priority**: P1 (Core feature - User Story 1)

**Independent Test**: Create EnhancedConclusion object, pass to writer, verify output markdown matches spec format with all sections and evidence references properly formatted.

**Included Subtasks**:
- [x] T035: Create `src/utils/enhanced_conclusion_writer.py` with EnhancedConclusionWriter class
- [x] T036: Implement `_format_verdict_section()` with answer, confidence, rationale, room outcomes (120-150 words)
- [x] T037: Implement `_format_role_analysis_section()` with 3-5 bullets each and evidence references
- [x] T038: Implement `_format_gaps_section()` and `_format_recommendations_section()` with proper formatting
- [x] T039: Implement `_format_evidence_reference()` to display [room_id, speaker_role, turn_index, quote]
- [x] T040: [P] Create unit tests in `tests/test_enhanced_conclusion/test_enhanced_writer.py`

**Implementation Sketch**:
1. Create EnhancedConclusionWriter class (separate from existing ConclusionWriter)
2. Implement `write(enhanced_conclusion: EnhancedConclusion, output_path: str) -> str`
3. Format sections per spec structure:
   - "# Enhanced Conclusion: <Debate Question>"
   - "## Verdict" with Answer, Confidence, Rationale, Room Outcomes
   - "## Analysis by Role" with subsections per role
   - "## Critical Gaps Identified" with ranked list (max 5)
   - "## Action Plan" with High/Medium/Low subsections
   - "## Metadata"
4. Format evidence references as: [room_id, speaker_role, turn_index, "quote..."]
5. Enforce length limits in formatting (truncate if needed)
6. Write tests for markdown format validation

**Parallel Opportunities**: Can run in parallel with WP06 (both work with EnhancedConclusion model)

**Dependencies**: WP01, WP06

**Risks**:
- Must handle empty lists (no gaps, no recommendations)
- Evidence reference format must match spec exactly
- UTF-8 encoding for Russian/English content

**Estimated Prompt Size**: ~350 lines

---

## WP08: Pipeline Integration in ConclusionReportNode

**Goal**: Integrate enhanced conclusion pipeline into existing ConclusionReportNode with proper routing for committee debates.

**Priority**: P1 (Integration - enables end-to-end functionality)

**Independent Test**: Run complete committee debate and verify enhanced conclusion.md is generated in committee_output/{run_id}/ with all sections.

**Included Subtasks**:
- [x] T041: Update `src/nodes/conclusion_report_node.py` to detect committee debates and route to enhanced pipeline
- [x] T042: Implement `_run_enhanced_pipeline()` that orchestrates Stage 1 → Stage 2 → Writer
- [x] T043: Add final_report.md reading logic for committee debates (single source of truth)
- [x] T044: Update output path to write to `committee_output/{run_id}/conclusion.md`
- [x] T045: [P] Create integration test in `tests/test_enhanced_conclusion/test_pipeline_integration.py`

**Implementation Sketch**:
1. Modify ConclusionReportNode.__call__() to detect committee debate type
2. If committee debate:
   - Read final_report.md from committee_output/{run_id}/
   - Run Stage 1A: VerdictExtractor(final_report) → Verdict
   - Run Stage 1B: RoleAnalyzer(final_report) → RoleAnalysis[]
   - Build IntermediateConclusionSchema
   - Run Stage 2: GapRecommendationGenerator(schema) → gaps, recommendations
   - Build EnhancedConclusion
   - Write using EnhancedConclusionWriter to committee_output/{run_id}/conclusion.md
3. If standard/document debate: use existing logic
4. Handle errors gracefully (fallback to basic conclusion if enhanced fails)
5. Write integration test with mock final_report.md

**Parallel Opportunities**: None (integration)

**Dependencies**: WP03, WP04, WP06, WP07

**Risks**:
- Must not break existing standard/document debate flows
- Error handling if enhanced pipeline fails
- Performance target: < 10 seconds (FR-028)

**Estimated Prompt Size**: ~320 lines

---

## WP09: Committee Debate Final Report Extractor

**Goal**: Create extractor for parsing committee debate final_report.md to extract room outcomes and transcript data.

**Priority**: P1 (Core feature - enables committee debate analysis)

**Independent Test**: Pass sample final_report.md from committee debate and verify extractor correctly parses all rooms, winners, and provides access to transcript data.

**Included Subtasks**:
- [x] T046: Create `src/extractors/committee_report_extractor.py` with CommitteeReportExtractor class
- [x] T047: Implement `_parse_room_sections()` to identify each debate room (TPM_vs_CPO, TPM_vs_CFO, etc.)
- [x] T048: Implement `_extract_room_outcomes()` to get winner from each room
- [x] T049: Implement `_extract_transcript_data()` to provide structured access for evidence extraction
- [x] T050: [P] Create unit tests in `tests/test_enhanced_conclusion/test_committee_extractor.py`

**Implementation Sketch**:
1. Create CommitteeReportExtractor class
2. Implement `parse(final_report_path: str) -> CommitteeReportData`
3. Parse markdown structure:
   - Split by room headers (e.g., "## TPM vs CPO")
   - Extract winner/loser from each room
   - Extract judge verdict and rationale
   - Extract transcript with turn indices
4. Return structured data with:
   - room_outcomes: dict mapping room_id to winner
   - judge_rationales: list of rationale texts
   - transcripts: dict mapping room_id to list of turns
5. Write tests with sample final_report.md

**Parallel Opportunities**: Can run in parallel with WP01, WP02

**Dependencies**: None

**Risks**:
- final_report.md format may vary
- Must handle missing rooms or incomplete data
- Transcript format must support turn indexing

**Estimated Prompt Size**: ~300 lines

---

## WP10: Length & Evidence Validation

**Goal**: Implement validation infrastructure for FR-030 (length limits) and FR-031 (evidence references) with contract tests.

**Priority**: P1 (Quality - ensures spec compliance)

**Independent Test**: Run validation suite and verify 100% evidence reference completeness and all length limits enforced.

**Included Subtasks**:
- [x] T051: Create `src/validators/enhanced_conclusion_validators.py` with validation functions
- [x] T052: Implement `validate_evidence_references()` to check all required fields present (room_id, speaker_role, turn_index, quote)
- [x] T053: Implement `validate_length_limits()` to check verdict word count, 3-5 bullets per role, max 5 gaps, max 5 high-priority recommendations
- [x] T054: Implement `validate_recommendation_format()` to ensure problem→action→metric structure
- [x] T055: [P] Create contract tests in `tests/contract/test_evidence_references.py` and `tests/contract/test_length_validation.py`

**Implementation Sketch**:
1. Create validators module
2. Implement `validate_evidence_references(enhanced_conclusion: EnhancedConclusion) -> ValidationResult`
   - Check every evidence reference has: room_id, speaker_role, turn_index, quote
   - Verify quote length <= 200 chars
   - Return detailed validation report
3. Implement `validate_length_limits(enhanced_conclusion: EnhancedConclusion) -> ValidationResult`
   - Verdict answer: 120-150 words
   - Each role: 3-5 strengths, 3-5 weaknesses
   - Max 5 critical gaps
   - Max 5 high-priority recommendations
4. Implement `validate_recommendation_format(recommendations: List[Recommendation]) -> ValidationResult`
   - Each has: problem, action, metric
   - Metric is measurable
5. Write contract tests that enforce 100% compliance

**Parallel Opportunities**: Can run in parallel with WP06, WP07

**Dependencies**: WP01, WP03, WP04, WP06

**Risks**:
- Validation must not be too strict (allow valid edge cases)
- Must provide clear error messages for validation failures

**Estimated Prompt Size**: ~380 lines

---

## WP11: Integration & E2E Testing

**Goal**: Create end-to-end tests and ensure complete integration with committee debate workflow.

**Priority**: P1 (Validation - confirms feature works end-to-end)

**Independent Test**: Run full committee debate with enhanced conclusion and verify complete output with all sections and proper formatting.

**Included Subtasks**:
- [x] T056: Create `tests/integration/test_committee_conclusion_enhanced.py` for full workflow test
- [x] T057: Create sample final_report.md fixtures for testing various scenarios (unanimous, split, tie)
- [x] T058: Implement performance test to verify < 10 second generation time (FR-028)
- [x] T059: Add manual validation scenario for readability test (can user read in < 60 seconds per SC-001)
- [x] T060: [P] Update existing E2E tests to accommodate enhanced conclusion format

**Implementation Sketch**:
1. Create E2E test that:
   - Runs full committee debate (4 rooms)
   - Waits for completion
   - Verifies enhanced conclusion.md exists
   - Validates all sections present
   - Validates all evidence references complete
   - Validates all length limits respected
2. Create fixtures:
   - unanimous_final_report.md (4-0 outcome)
   - split_final_report.md (3-1 outcome)
   - tie_final_report.md (2-2 outcome)
   - minimal_final_report.md (edge case)
3. Implement performance test:
   - Time enhanced conclusion generation
   - Assert < 10 seconds for typical 4-room debate
4. Create manual test script for readability:
   - Time user reading enhanced conclusion
   - Target: < 60 seconds
5. Update existing tests in `tests/test_full_workflow.py` to handle new format

**Parallel Opportunities**: None (final integration)

**Dependencies**: WP08, WP09, WP10

**Risks**:
- E2E tests may be flaky if LLM responses vary
- Performance test may fail on slow systems
- Need to handle both Russian and English content

**Estimated Prompt Size**: ~340 lines

---

## Success Criteria Validation

Each work package includes specific validation criteria:

### Functional Requirements Coverage
- FR-001 to FR-004 (Verdict): Covered by WP03, WP05
- FR-005 to FR-009 (Role Analysis): Covered by WP04
- FR-010 to FR-012 (Critical Gaps): Covered by WP06
- FR-013 to FR-017 (Recommendations): Covered by WP06
- FR-018 to FR-022 (Content & Structure): Covered by WP07, WP08
- FR-023 to FR-025 (Extensibility): Covered by WP02 (role-agnostic base)
- FR-026 to FR-031 (Quality): Covered by WP10

### Success Criteria Coverage
- SC-001 (60-second readability): Covered by WP07 (length limits), WP11 (manual test)
- SC-002 (100% metrics): Covered by WP06 (recommendation format), WP10 (validation)
- SC-003 (95% traceability): Covered by WP04, WP06 (evidence extraction), WP10 (validation)
- SC-004 (< 10 seconds): Covered by WP11 (performance test)
- SC-005 (no generic recommendations): Covered by WP06 (evidence grounding)
- SC-006 (90% accuracy): Covered by WP11 (E2E validation)
- SC-007 (100% evidence fields): Covered by WP10 (contract tests)

---

## Dependencies Graph

```
WP01 (Pydantic Types) ──────────────────────────────┐
                                                    │
WP02 (Analyzer Base) ───────────────────────────┐   │
                                                 │   │
WP09 (Committee Extractor) ─────────────────┐   │   │
                                              │   │   │
WP03 (Verdict Extractor) ──────────────────┐ │   │   │
WP04 (Role Analyzer) ──────────────────────┤ │   │   │
WP05 (Confidence Calculator) ──────────────┤ │   │   │
                                             │ │   │   │
                                             ▼ ▼   ▼   ▼
                                           WP06 (Gap & Rec Generator)
                                                  │
WP10 (Validation) ──────────────────────────────┤ │
                                                  │ │
WP07 (Enhanced Writer) ──────────────────────────┤ │
                                                    │
                                                  WP08 (Pipeline Integration)
                                                        │
                                                      WP11 (E2E Testing)
```

**Parallel Execution Groups**:
- Group 1 (Foundation): WP01, WP02, WP09
- Group 2 (Stage 1): WP03, WP04, WP05
- Group 3 (Quality): WP10 (can run parallel to WP06, WP07)
- Group 4 (Stage 2 & Writer): WP06, WP07
- Group 5 (Integration): WP08
- Group 6 (Final): WP11

---

## MVP Scope Recommendation

**Minimum Viable Product**: WP01 through WP08

This provides:
- Complete enhanced conclusion pipeline
- Verdict with confidence
- Role-based analysis with evidence
- Critical gaps and prioritized recommendations
- Integration with committee debate workflow

**Post-MVP**: WP09, WP10, WP11 add polish, validation, and comprehensive testing

---

## Notes for Implementers

1. **Evidence References**: Every insight MUST include room_id, speaker_role, turn_index, quote (max 200 chars) per FR-031. This is non-negotiable for traceability.

2. **Length Limits**: FR-030 enforces 60-second readability:
   - Verdict: 120-150 words max
   - Per role: 3-5 strengths, 3-5 weaknesses
   - Critical gaps: max 5
   - High-priority recommendations: max 5

3. **Confidence Formula**: FR-029 is explicit:
   - Unanimous (4-0 or 0-4) = High
   - Split (3-1 or 1-3) = Medium
   - Tie (2-2) = Low
   - Strong contradictions reduce by 1 level

4. **Recommendation Format**: Must follow "Problem → Action → Metric" per FR-014. Metric must be measurable.

5. **File Output**: Enhanced conclusion.md goes to `committee_output/{run_id}/conclusion.md` (same directory as final_report.md).

6. **Single Source of Truth**: final_report.md is the ONLY input for enhanced conclusion. No direct state access for committee debates.

7. **Error Handling**: If enhanced pipeline fails, fall back to basic conclusion. Feature 009 infrastructure must remain functional.

8. **Performance Target**: < 10 seconds for typical 4-room committee debate (FR-028).

---

*Tasks generated: 2025-02-16*
*Next step: Generate WP prompt files*
