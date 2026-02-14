# Implementation Plan: Debate Conclusion Report

**Branch**: `009-debate-conclusion-report` | **Date**: 2025-02-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/kitty-specs/009-debate-conclusion-report/spec.md`

## Summary

This feature adds a post-processing step that generates a structured Conclusion.md file after each debate completes. The conclusion report extracts key information from final_report.md (the single source of truth) and provides:

1. **Q&A Summary**: 3-10 key question-answer pairs from the debate
2. **Final Verdict**: Winner information with summary
3. **TPM Victory Analysis**: Key weaknesses in TPM's position and actionable improvements
4. **Agent Recommendations**: Attributed recommendations from each debate participant

The implementation follows the existing node/component pattern in the codebase and integrates as a separate post-processing step after the judge verdict.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**:
- LangGraph (workflow orchestration)
- LangChain (LLM chains)
- OpenAI API (LLM provider)
- Existing BaseComponent pattern from `nodes/base_component.py`

**Storage**: File-based (Conclusion.md written to debate output directory)
**Testing**: pytest (following existing test patterns in `tests/`)
**Target Platform**: Cross-platform (Linux, macOS, Windows)
**Project Type**: Single Python project with modular nodes
**Performance Goals**:
- Generation time: <5 seconds from debate completion (SC-005)
- Reading time: <2 minutes for complete review (SC-001)
- Success rate: 100% of completed debates (SC-002)

**Constraints**:
- Must use final_report.md as single source of truth
- Must support both standard and document-based debates
- Must handle multi-language content (preserve original language)
- Must be re-runnable without repeating debates

**Scale/Scope**:
- 2 workflow files to modify (standard and document-based)
- 1 new node to create
- 1 new prompt file to add
- Integration with existing debate state management
- Test coverage for both debate types

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on `.kittify/memory/constitution.md`:

| Requirement | Status | Notes |
|-------------|--------|-------|
| Python 3.12+ | ✅ Pass | Project uses Python 3.12+ |
| pytest required | ✅ Pass | E2E tests exist in tests/ |
| Cross-platform | ✅ Pass | File-based output works on all platforms |
| TDD approach | ⚠️ Action | Write tests before implementation |
| Minimal dependencies | ✅ Pass | Uses existing LangChain/LangGraph stack |
| Spec-driven | ✅ Pass | Implementation from approved spec |

**Action Required**: Follow TDD - write failing tests first before implementing the conclusion node.

## Project Structure

### Documentation (this feature)

```
kitty-specs/009-debate-conclusion-report/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (implementation plan)
├── research.md          # Phase 0: Technical research (TO BE CREATED)
├── data-model.md        # Phase 1: Data structures (TO BE CREATED)
├── quickstart.md        # Phase 1: Developer guide (TO BE CREATED)
├── contracts/           # Phase 1: Interface definitions
│   └── conclusion_report_contract.py  # TO BE CREATED
└── tasks.md             # Phase 2: Work packages (TO BE CREATED by /spec-kitty.tasks)
```

### Source Code (repository root)

```
src/
├── nodes/
│   ├── base_component.py          # Existing base class
│   ├── conclusion_report_node.py  # NEW: Conclusion generator node
│   └── ...
├── workflow/
│   ├── debate_workflow.py          # MODIFY: Add conclusion node
│   └── document_debate_workflow.py # MODIFY: Add conclusion node
├── prompts/
│   ├── conclusion_report_prompt.md # NEW: Prompt for conclusion generation
│   └── ...
└── ...
```

**Structure Decision**: Single project structure following existing node pattern. The conclusion report node inherits from `BaseComponent` and integrates into both workflow graphs after the judge verdict.

## Architecture Overview

### Component Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│                    Debate Workflow                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  topic_gen → opening → fact_check → rebuttal → fact_check →    │
│  counter → fact_check → final_arg → fact_check → JUDGE →       │
│                                                              │
│                                                         ┌──────▼──────┐
│                                                         │ Conclusion  │
│                                                         │ Report Node │
│                                                         └──────┬──────┘
│                                                                │
│                                                         ┌──────▼──────┐
│                                                         │  Write      │
│                                                         │ Conclusion  │
│                                                         │.md          │
│                                                         └─────────────┘
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
final_report.md (immutable source)
         │
         ▼
┌──────────────────────────┐
│ ConclusionReportNode     │
│  - Parse final_report.md │
│  - Extract Q&A pairs     │
│  - Identify verdict      │
│  - Analyze TPM position  │
│  - Generate recs         │
└──────────────────────────┘
         │
         ▼
   Conclusion.md
   (structured output)
```

### Key Design Decisions

1. **Post-processing pattern**: Conclusion generation is a separate step that runs AFTER final_report.md is complete
2. **Source of truth**: All analysis builds from final_report.md - no reprocessing of debate history
3. **Reusability**: The node can be called independently to regenerate Conclusion.md without repeating debates
4. **State integration**: Conclusion data added to debate state for potential downstream use

## Phase 0: Research Tasks

### Technical Research Questions

1. **final_report.md Structure Analysis**
   - Document exact structure of final_report.md
   - Identify parsing strategy for each section
   - Map report sections to conclusion sections

2. **TPM Role Detection**
   - How to identify which agent is TPM in different debate configurations
   - Handle standard PRO/CON debates vs role-based committees

3. **Q&A Extraction Strategy**
   - How to identify "key" Q&A pairs vs full log
   - Determine aggregation approach for similar questions

4. **Weakness Detection Pattern**
   - How to extract TPM weaknesses from final_report
   - Distinguish between TPM's own acknowledgments vs others' critiques

### Research Artifacts

Create `research.md` with:
- final_report.md structure documentation
- Parsing strategy for each section
- TPM role detection algorithm
- Q&A extraction heuristics
- Sample Conclusion.md output examples

## Phase 1: Design Tasks

### Data Model Design

Create `data-model.md` with:
- `ConclusionData` TypedDict structure
- `Recommendation` entity definition
- `TPMWeakness` entity definition
- `VerdictSummary` entity definition

### Contract Definitions

Create `contracts/conclusion_report_contract.py` with:
```python
from typing import TypedDict, List, Optional

class Recommendation(TypedDict):
    """A recommendation from a debate participant"""
    agent_role: str  # "TPM", "BDM", "CPO", etc.
    text: str  # Recommendation content
    priority: Optional[str]  # Optional priority level

class TPMWeakness(TypedDict):
    """A weakness identified in TPM's position"""
    category: str  # e.g., "unjustified assumption", "uncovered risk"
    description: str  # Description of the weakness
    severity: Optional[str]  # Optional severity level

class VerdictSummary(TypedDict):
    """The debate verdict"""
    winner: str  # Role name or "No clear winner"
    summary: str  # 1-3 sentence explanation

class ConclusionData(TypedDict):
    """Complete conclusion report data"""
    debate_question: str
    verdict: VerdictSummary
    qa_summary: List[tuple[str, str]]  # (question, answer) pairs
    tpm_weaknesses: List[TPMWeakness]
    recommended_improvements: List[str]
    recommendations_by_agent: List[Recommendation]
```

### Quickstart Guide

Create `quickstart.md` with:
- How to run a debate with conclusion generation
- How to manually regenerate Conclusion.md
- How to test the conclusion node
- Example Conclusion.md output

## Phase 2: Implementation Tasks

### Work Package Breakdown

#### WP01: Create Conclusion Report Node (P1)
- Create `nodes/conclusion_report_node.py`
- Inherit from `BaseComponent`
- Implement `__call__` method
- Add token tracking
- Handle error cases

#### WP02: Create Conclusion Prompt (P1)
- Create `prompts/conclusion_report_prompt.md`
- Define system prompt for conclusion generation
- Include structure requirements
- Add examples for few-shot learning

#### WP03: Integrate into Standard Workflow (P1)
- Modify `workflow/debate_workflow.py`
- Add ConclusionReportNode to graph
- Add edge from judge_node to conclusion_report_node
- Update state transitions

#### WP04: Integrate into Document Workflow (P1)
- Modify `workflow/document_debate_workflow.py`
- Add ConclusionReportNode to graph
- Add edge from judge_node to conclusion_report_node
- Handle document context

#### WP05: Implement Conclusion Writer (P2)
- Create `utils/conclusion_writer.py`
- Implement markdown formatting
- Handle file I/O
- Add error handling for missing directories

#### WP06: Add E2E Tests (P1)
- Create `tests/test_conclusion_report_node.py`
- Test standard debate conclusion generation
- Test document debate conclusion generation
- Test edge cases (no winner, no recommendations)
- Test multi-language handling

### Implementation Order

1. **WP01** + **WP02** (parallel): Create node and prompt
2. **WP06**: Write failing tests (TDD)
3. **WP01** implementation: Make tests pass
4. **WP05**: Create writer utility
5. **WP03**: Integrate into standard workflow
6. **WP04**: Integrate into document workflow
7. **WP06**: Add workflow integration tests

## Testing Strategy

### Unit Tests
- Test individual parsing functions
- Test markdown formatting
- Test data structure validation

### Integration Tests
- Test node integration with workflow
- Test file output generation
- Test error handling

### E2E Tests
- Test complete debate → conclusion flow
- Test both debate types
- Test all edge cases

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| final_report.md format changes | Parse defensively, handle missing sections |
| TPM role not identifiable | Default to first PRO agent if TPM not found |
| Multi-language content | Preserve original language, don't translate |
| File system errors | Handle permissions, create directories, explicit errors |
| Performance degradation | Cache parsed data, stream output |

## Success Criteria Validation

- ✅ SC-001: <2 min reading time (achieved via structured format)
- ✅ SC-002: 100% generation success (error handling)
- ✅ SC-003: 90% actionable (prompt engineering)
- ✅ SC-004: 100% attribution accuracy (role mapping)
- ✅ SC-005: <5 sec generation (efficient parsing)

## Next Steps

1. **Execute Phase 0**: Run `/spec-kitty.research` to create research.md
2. **Execute Phase 1**: Create design artifacts (data-model.md, quickstart.md, contracts/)
3. **Execute Phase 2**: Run `/spec-kitty.tasks` to generate work packages
4. **Implement**: Use `/spec-kitty.implement WP##` for each work package
