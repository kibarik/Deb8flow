# Implementation Plan: Enhanced Committee Debate Conclusion Report

**Branch**: `011-enhanced-committee-debate-conclusion` | **Date**: 2025-02-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/kitty-specs/011-enhanced-committee-debate-conclusion/spec.md`

---

## Summary

Transform the conclusion report from a generic summary into an actionable product improvement plan by implementing a hybrid multi-step LLM pipeline that:
1. Extracts verdict with confidence level using explicit formula (FR-029)
2. Performs structured role-based analysis (strengths/weaknesses with evidence)
3. Identifies cross-role critical gaps ranked by severity
4. Generates prioritized "problem → action → metric" recommendations

**Technical Approach**: Hybrid multi-step pipeline - Stage 1 uses dedicated prompts for verdict/role extraction, Stage 2 processes structured intermediate schema for gap identification and recommendations.

---

## Technical Context

**Language/Version**: Python 3.12+ with asyncio support
**Primary Dependencies**: LangGraph, langchain-core, langchain-openai, pydantic
**Storage**: File-based (reads final_report.md, writes conclusion.md to committee_output/{run_id}/)
**Testing**: pytest for critical path coverage
**Target Platform**: Cross-platform CLI utility (Linux, macOS, Windows)
**Project Type**: Single project with modular nodes architecture
**Performance Goals**: < 10 seconds report generation time (FR-028), < 60 seconds reading time (SC-001)
**Constraints**: Must extend Feature 009 infrastructure, single source of truth (final_report.md), role-agnostic core for extensibility
**Scale/Scope**: Typical committee debate (4 rooms), max 5 gaps, max 5 high-priority recommendations

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Standards Compliance

| Requirement | Status | Notes |
|-------------|--------|-------|
| Python 3.12+ | ✅ PASS | Extends existing Python 3.12+ codebase |
| pytest required | ✅ PASS | Tests will cover critical extraction and generation paths |
| Spec-driven development | ✅ PASS | Working from approved spec (337 lines, 31 FRs) |
| TDD approach | ✅ PASS | Will write tests before implementation |
| Minimal dependencies | ✅ PASS | Uses existing LangGraph/LangChain stack; no new major dependencies |
| Cross-platform CLI | ✅ PASS | File I/O operations; platform-agnostic |
| Self-documenting code | ✅ PASS | Clear type hints and descriptive names per project standards |

### Quality Gates

| Gate | Status | Justification |
|------|--------|---------------|
| CI green only | ✅ PASS | Will ensure tests pass before merge |
| Spec compliance | ✅ PASS | Implementation will follow spec.md requirements |
| Tests added | ✅ PASS | Test coverage for extraction, generation, validation |

**Constitution Status**: ✅ **ALL GATES PASSED** - No violations, no exceptions needed

---

## Project Structure

### Documentation (this feature)

```
kitty-specs/011-enhanced-committee-debate-conclusion/
├── spec.md              # Feature specification (31 FRs, 7 SCs)
├── plan.md              # This file
├── research.md          # Phase 0: LLM prompting research
├── data-model.md        # Phase 1: Intermediate schema definitions
├── quickstart.md        # Phase 1: Developer quickstart guide
├── contracts/           # Phase 1: Analysis contracts (not applicable - internal LLM calls)
└── tasks.md             # Phase 2: Work packages (NOT created by this command)
```

### Source Code (repository root)

```
src/
├── nodes/
│   └── conclusion_report_node.py         # ENHANCE: Add enhanced analysis pipeline
├── types/
│   └── conclusion_types.py               # ENHANCE: Add intermediate schema types
├── extractors/
│   └── debate_state_extractor.py         # ENHANCE: Add structured extraction for role analysis
├── utils/
│   └── conclusion_writer.py              # ENHANCE: Add enhanced markdown writer
├── prompts/
│   ├── conclusion_report_prompt.py       # ENHANCE: Add new prompt templates
│   └── verdict_extraction_prompt.md      # NEW: Stage 1A - Verdict extraction
│   └── role_analysis_prompt.md           # NEW: Stage 1B - Role-based analysis
│   └── gap_recommendation_prompt.md      # NEW: Stage 2 - Gaps & recommendations
└── analyzers/                            # NEW: Analysis pipeline components
    ├── verdict_analyzer.py               # NEW: Verdict extraction with confidence calculation
    ├── role_analyzer.py                  # NEW: Role-based strength/weakness extraction
    ├── gap_identifier.py                 # NEW: Cross-role gap identification
    └── recommendation_generator.py       # NEW: Prioritized recommendation generation

tests/
├── test_enhanced_conclusion/
│   ├── test_verdict_analyzer.py          # NEW: Test verdict extraction & confidence calculation
│   ├── test_role_analyzer.py             # NEW: Test role-based analysis extraction
│   ├── test_gap_identifier.py            # NEW: Test cross-role gap identification
│   ├── test_recommendation_generator.py  # NEW: Test recommendation generation
│   └── test_integration.py               # NEW: End-to-end enhanced conclusion test
├── contract/
│   └── test_evidence_references.py       # NEW: Test FR-031 compliance
└── integration/
    └── test_committee_conclusion.py      # NEW: Full committee debate workflow test
```

**Structure Decision**: Single project structure extending existing nodes architecture. New `analyzers/` directory encapsulates the hybrid pipeline stages while maintaining compatibility with existing `BaseComponent` pattern.

---

## Architecture Design

### Hybrid Multi-Step Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    Enhanced Conclusion Pipeline                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   final_report.md     │
                    │   (Single Source)      │
                    └───────────────────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────┐
        │            STAGE 1: Extraction            │
        ├───────────────────────────────────────────┤
        │                                           │
        │  ┌─────────────────┐  ┌───────────────┐ │
        │  │ Verdict         │  │ Role Analysis  │ │
        │  │ Extractor       │  │ Extractor      │ │
        │  │ (LLM Prompt)    │  │ (LLM Prompt)   │ │
        │  └────────┬────────┘  └───────┬───────┘ │
        │           │                    │         │
        │           └────────┬───────────┘         │
        │                    │                     │
        └────────────────────┼─────────────────────┘
                             │
                             ▼
              ┌─────────────────────────────┐
              │   Intermediate Schema        │
              │   (Pydantic models)          │
              │                             │
              │  - Verdict + confidence      │
              │  - RoleAnalysis[]            │
              │    - role_name               │
              │    - strengths[] (3-5 max)  │
              │    - weaknesses[] (3-5 max) │
              │    - evidence_refs[]         │
              └─────────────────────────────┘
                             │
                             ▼
        ┌───────────────────────────────────────────┐
        │         STAGE 2: Synthesis               │
        ├───────────────────────────────────────────┤
        │                                           │
        │  ┌─────────────────────────────────┐     │
        │  │ Gap & Recommendation Generator   │     │
        │  │ (Single LLM Prompt)              │     │
        │  │                                   │     │
        │  │ Input: Intermediate Schema        │     │
        │  │ Output:                           │     │
        │  │   - CriticalGap[] (max 5)         │     │
        │  │   - Recommendation[] (prioritized)│ │
        │  └─────────────────────────────────┘     │
        │                                           │
        └───────────────────────────────────────────┘
                             │
                             ▼
              ┌─────────────────────────────┐
              │   Enhanced Conclusion        │
              │   Writer                     │
              └─────────────────────────────┘
                             │
                             ▼
              ┌─────────────────────────────┐
              │   committee_output/{run_id}/ │
              │   conclusion.md              │
              └─────────────────────────────┘
```

### Key Design Decisions

1. **Two-Stage Pipeline**: Separates extraction (Stage 1) from synthesis (Stage 2) for better modularity and debugging
2. **Structured Intermediate Schema**: Pydantic models ensure type safety and validate LLM outputs
3. **Dedicated Prompts**: Stage 1 uses specialized prompts for verdict and role analysis; Stage 2 synthesizes cross-role insights
4. **Evidence Tracing**: Every insight includes room_id, speaker_role, turn_index, quote (max 200 chars) per FR-031
5. **Length Enforcement**: Each stage enforces limits (3-5 bullets per role, max 5 gaps, max 5 high-priority recommendations)

---

## Phase 0: Research

### Research Tasks

**Completed**: Specification clarifications resolved (file location, confidence formula, length limits, evidence format)

**Outstanding Research**: None - all technical decisions documented in spec

**Research Output**: Skip research.md - all requirements sufficiently specified for implementation

---

## Phase 1: Design

### Data Model

See [data-model.md](./data-model.md) for complete schema definitions.

**Key Entities**:

```python
# Intermediate Schema (Stage 1 Output)
class EvidenceReference(BaseModel):
    room_id: str
    speaker_role: str
    turn_index: int
    quote: str  # max 200 chars

class Strength(BaseModel):
    description: str
    evidence: EvidenceReference

class Weakness(BaseModel):
    description: str
    evidence: EvidenceReference

class RoleAnalysis(BaseModel):
    role_name: str  # TPM, CPO, CFO, CTO, BDM
    strengths: List[Strength]  # 3-5 max
    weaknesses: List[Weakness]  # 3-5 max

class Verdict(BaseModel):
    answer: str
    confidence: Literal["High", "Medium", "Low"]
    rationale: str
    room_outcomes: str

class IntermediateConclusionSchema(BaseModel):
    verdict: Verdict
    role_analyses: List[RoleAnalysis]

# Stage 2 Output
class CriticalGap(BaseModel):
    title: str
    severity: Literal["High", "Medium", "Low"]
    description: str
    sources: List[str]  # role names
    evidence: List[EvidenceReference]

class Recommendation(BaseModel):
    priority: Literal["High", "Medium", "Low"]
    problem: str
    action: str
    metric: str
    source_evidence: EvidenceReference

class EnhancedConclusion(BaseModel):
    verdict: Verdict
    role_analyses: List[RoleAnalysis]
    critical_gaps: List[CriticalGap]  # max 5
    recommendations: List[Recommendation]
```

### Contracts

**Internal LLM Contracts** (not external API contracts):

| Stage | Input | Output | Prompt File |
|-------|-------|--------|-------------|
| Stage 1A | final_report.md text | Verdict Pydantic model | verdict_extraction_prompt.md |
| Stage 1B | final_report.md text | RoleAnalysis[] Pydantic models | role_analysis_prompt.md |
| Stage 2 | IntermediateConclusionSchema | CriticalGap[], Recommendation[] | gap_recommendation_prompt.md |

### Quickstart

See [quickstart.md](./quickstart.md) for developer onboarding guide.

---

## Implementation Phases

### Phase 1: Core Pipeline (Priority: P1)

**Goal**: Implement hybrid multi-step pipeline with basic functionality

**Deliverables**:
1. Create `src/analyzers/` directory structure
2. Implement `VerdictExtractor` with confidence calculation (FR-029)
3. Implement `RoleAnalyzer` with evidence extraction (FR-031)
4. Implement `GapIdentifier` for cross-role gap analysis
5. Implement `RecommendationGenerator` with prioritization
6. Create Pydantic models in `src/types/conclusion_types.py`
7. Update `ConclusionReportNode` to use enhanced pipeline
8. Write integration tests for full pipeline

**Acceptance**: Enhanced conclusion.md generated with all required sections

### Phase 2: Length Validation (Priority: P1)

**Goal**: Enforce FR-030 length limits

**Deliverables**:
1. Add validation to `RoleAnalyzer` (3-5 bullets max per role)
2. Add validation to `GapIdentifier` (max 5 gaps)
3. Add validation to `RecommendationGenerator` (max 5 high-priority)
4. Add word count validation to `VerdictExtractor` (120-150 words)
5. Write tests for length constraint enforcement

**Acceptance**: All sections respect length limits, 60-second readability achievable

### Phase 3: Evidence Tracing (Priority: P1)

**Goal**: Implement FR-031 evidence reference format

**Deliverables**:
1. Update all analyzers to extract room_id, speaker_role, turn_index
2. Implement quote truncation (max 200 chars)
3. Update markdown writer to format evidence references
4. Write contract tests for evidence reference completeness

**Acceptance**: 100% of insights include required evidence fields (SC-007)

### Phase 4: Extensibility (Priority: P2)

**Goal**: Implement FR-022 through FR-025 for role-agnostic core

**Deliverables**:
1. Refactor pipeline to support pluggable role definitions
2. Add configuration for custom committee roles
3. Create role-agnostic analysis interface
4. Write tests for custom role support

**Acceptance**: Pipeline supports non-standard roles without code changes

---

## Testing Strategy

### Unit Tests

| Component | Test Coverage | Key Scenarios |
|-----------|---------------|---------------|
| VerdictExtractor | Confidence calculation logic | Unanimous (4-0), Split (3-1), Tie (2-2), Contradictions |
| RoleAnalyzer | Extraction & length limits | 3-5 bullets, evidence completeness, multi-room patterns |
| GapIdentifier | Cross-role analysis | Severity ranking, source attribution, max 5 gaps |
| RecommendationGenerator | Prioritization & format | Problem→Action→Metric, max 5 high-priority |
| ConclusionWriter | Markdown formatting | All sections, evidence references, length limits |

### Integration Tests

- `test_committee_conclusion_full.py`: End-to-end committee debate workflow
- `test_evidence_references.py`: FR-031 compliance verification
- `test_length_validation.py`: FR-030 constraint enforcement
- `test_confidence_calculation.py`: FR-029 formula correctness

### Contract Tests

- Evidence reference completeness (SC-007: 100% compliance)
- Length limit enforcement (SC-001: 60-second readability)
- Recommendation format (SC-002: 100% metric population)
- Traceability (SC-003: 95% traceable to debate content)

---

## Open Questions

**None** - All clarifications resolved during specification phase.

---

## Dependencies

### Blocking
- Feature 009 (Debate Conclusion Report) must be complete
- final_report.md generation must be stable

### Non-Blocking
- Standard/document debate support (deferred to future phases per scope)

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Report generation time | < 10 seconds | FR-028, SC-004 |
| Reading time | < 60 seconds | FR-030, SC-001 |
| Evidence completeness | 100% | SC-007, FR-031 |
| Recommendation traceability | 95% | SC-003, FR-026 |
| Role analysis accuracy | 90% | SC-006 |
| User actionability rating | 80%+ | QI-001 |

---

*Plan generated: 2025-02-16*
*Next step: `/spec-kitty.tasks` to generate work packages*
